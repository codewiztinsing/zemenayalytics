"""
Management command to backfill time series aggregates from existing data.

Usage:
    python manage.py backfill_time_series
    python manage.py backfill_time_series --granularity day
    python manage.py backfill_time_series --granularity hour --start-date 2025-01-01
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth, TruncYear
from datetime import datetime, timedelta

from analytics.models import BlogView, Blog
from analytics.models.time_series import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)
from config.logger import logger


class Command(BaseCommand):
    help = "Backfill time series aggregates from existing BlogView and Blog data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--granularity",
            type=str,
            choices=["hour", "day", "week", "month", "year", "all"],
            default="all",
            help="Granularity to backfill (default: all)",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            help="Start date for backfilling (YYYY-MM-DD). If not provided, uses earliest data.",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            help="End date for backfilling (YYYY-MM-DD). If not provided, uses current date.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing aggregates for the specified granularity before backfilling",
        )

    def handle(self, *args, **options):
        granularity = options["granularity"]
        start_date_str = options.get("start_date")
        end_date_str = options.get("end_date")
        clear = options.get("clear", False)

        # Determine which granularities to process
        if granularity == "all":
            granularities = ["hour", "day", "week", "month", "year"]
        else:
            granularities = [granularity]

        # Get date range
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            # Get earliest BlogView or Blog date
            earliest_view = BlogView.objects.order_by("viewed_at").first()
            earliest_blog = Blog.objects.order_by("created_at").first()
            
            if earliest_view and earliest_blog:
                start_date = min(earliest_view.viewed_at, earliest_blog.created_at)
            elif earliest_view:
                start_date = earliest_view.viewed_at
            elif earliest_blog:
                start_date = earliest_blog.created_at
            else:
                self.stdout.write(self.style.WARNING("No data found to backfill."))
                return

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            end_date = timezone.now()

        self.stdout.write(f"Backfilling time series aggregates from {start_date.date()} to {end_date.date()}")
        self.stdout.write(f"Granularities: {', '.join(granularities)}")

        for gran in granularities:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Processing granularity: {gran}")
            self.stdout.write(f"{'='*60}")

            if clear:
                self.stdout.write(f"Clearing existing {gran} aggregates...")
                if gran == "hour":
                    BlogViewTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.HOUR).delete()
                    BlogCreationTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.HOUR).delete()
                elif gran == "day":
                    BlogViewTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.DAY).delete()
                    BlogCreationTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.DAY).delete()
                elif gran == "week":
                    BlogViewTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.WEEK).delete()
                    BlogCreationTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.WEEK).delete()
                elif gran == "month":
                    BlogViewTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.MONTH).delete()
                    BlogCreationTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.MONTH).delete()
                elif gran == "year":
                    BlogViewTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.YEAR).delete()
                    BlogCreationTimeSeriesAggregate.objects.filter(granularity=TimeSeriesGranularity.YEAR).delete()
                self.stdout.write(self.style.SUCCESS(f"Cleared {gran} aggregates."))

            # Backfill blog views
            self._backfill_blog_views(gran, start_date, end_date)
            
            # Backfill blog creations
            self._backfill_blog_creations(gran, start_date, end_date)

        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("Backfilling completed!"))
        self.stdout.write(self.style.SUCCESS("="*60))

    def _backfill_blog_views(self, granularity: str, start_date: datetime, end_date: datetime):
        """Backfill blog view aggregates for a specific granularity."""
        self.stdout.write(f"\nBackfilling blog view aggregates ({granularity})...")

        # Map granularity to trunc function and enum
        trunc_map = {
            "hour": (TruncHour, TimeSeriesGranularity.HOUR),
            "day": (TruncDay, TimeSeriesGranularity.DAY),
            "week": (TruncWeek, TimeSeriesGranularity.WEEK),
            "month": (TruncMonth, TimeSeriesGranularity.MONTH),
            "year": (TruncYear, TimeSeriesGranularity.YEAR),
        }

        if granularity not in trunc_map:
            self.stdout.write(self.style.ERROR(f"Unknown granularity: {granularity}"))
            return

        trunc_func, gran_enum = trunc_map[granularity]

        # Aggregate blog views
        view_qs = BlogView.objects.filter(
            viewed_at__gte=start_date,
            viewed_at__lte=end_date
        )

        # Aggregate by time bucket and dimensions
        aggregates = (
            view_qs
            .annotate(time_bucket=trunc_func("viewed_at"))
            .values("time_bucket", "blog", "blog__country", "blog__author")
            .annotate(
                view_count=Count("id"),
                unique_blogs_viewed=Count("blog", distinct=True),
                unique_users=Count("user", distinct=True)
            )
            .order_by("time_bucket")
        )

        created_count = 0
        updated_count = 0

        for agg in aggregates:
            aggregate, created = BlogViewTimeSeriesAggregate.objects.update_or_create(
                granularity=gran_enum,
                time_bucket=agg["time_bucket"],
                blog_id=agg["blog"],
                country_id=agg["blog__country"],
                author_id=agg["blog__author"],
                defaults={
                    "view_count": agg["view_count"],
                    "unique_blogs_viewed": agg["unique_blogs_viewed"],
                    "unique_users": agg["unique_users"],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Create "all" aggregates (no filters)
        all_aggregates = (
            view_qs
            .annotate(time_bucket=trunc_func("viewed_at"))
            .values("time_bucket")
            .annotate(
                view_count=Count("id"),
                unique_blogs_viewed=Count("blog", distinct=True),
                unique_users=Count("user", distinct=True)
            )
            .order_by("time_bucket")
        )

        for agg in all_aggregates:
            aggregate, created = BlogViewTimeSeriesAggregate.objects.update_or_create(
                granularity=gran_enum,
                time_bucket=agg["time_bucket"],
                blog=None,
                country=None,
                author=None,
                defaults={
                    "view_count": agg["view_count"],
                    "unique_blogs_viewed": agg["unique_blogs_viewed"],
                    "unique_users": agg["unique_users"],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Created: {created_count}, Updated: {updated_count} blog view aggregates"
            )
        )

    def _backfill_blog_creations(self, granularity: str, start_date: datetime, end_date: datetime):
        """Backfill blog creation aggregates for a specific granularity."""
        self.stdout.write(f"\nBackfilling blog creation aggregates ({granularity})...")

        # Map granularity to trunc function and enum
        trunc_map = {
            "hour": (TruncHour, TimeSeriesGranularity.HOUR),
            "day": (TruncDay, TimeSeriesGranularity.DAY),
            "week": (TruncWeek, TimeSeriesGranularity.WEEK),
            "month": (TruncMonth, TimeSeriesGranularity.MONTH),
            "year": (TruncYear, TimeSeriesGranularity.YEAR),
        }

        if granularity not in trunc_map:
            self.stdout.write(self.style.ERROR(f"Unknown granularity: {granularity}"))
            return

        trunc_func, gran_enum = trunc_map[granularity]

        # Aggregate blog creations
        blog_qs = Blog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Aggregate by time bucket and dimensions
        aggregates = (
            blog_qs
            .annotate(time_bucket=trunc_func("created_at"))
            .values("time_bucket", "country", "author")
            .annotate(blog_count=Count("id"))
            .order_by("time_bucket")
        )

        created_count = 0
        updated_count = 0

        for agg in aggregates:
            aggregate, created = BlogCreationTimeSeriesAggregate.objects.update_or_create(
                granularity=gran_enum,
                time_bucket=agg["time_bucket"],
                country_id=agg["country"],
                author_id=agg["author"],
                defaults={"blog_count": agg["blog_count"]}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Create "all" aggregates (no filters)
        all_aggregates = (
            blog_qs
            .annotate(time_bucket=trunc_func("created_at"))
            .values("time_bucket")
            .annotate(blog_count=Count("id"))
            .order_by("time_bucket")
        )

        for agg in all_aggregates:
            aggregate, created = BlogCreationTimeSeriesAggregate.objects.update_or_create(
                granularity=gran_enum,
                time_bucket=agg["time_bucket"],
                country=None,
                author=None,
                defaults={"blog_count": agg["blog_count"]}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Created: {created_count}, Updated: {updated_count} blog creation aggregates"
            )
        )

