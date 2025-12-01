"""
Celery tasks for time series aggregation.

These tasks aggregate BlogView and Blog data at different granularities
and store them in the time series aggregate tables.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, F, Sum
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth, TruncYear
from celery import shared_task
from config.logger import logger

from apps.analytics.models import BlogView, Blog
from apps.analytics.models.time_series_aggregate import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)


def get_time_trunc_func(granularity: str):
    """Get the appropriate truncation function for a granularity."""
    trunc_map = {
        TimeSeriesGranularity.HOUR: TruncHour,
        TimeSeriesGranularity.DAY: TruncDay,
        TimeSeriesGranularity.WEEK: TruncWeek,
        TimeSeriesGranularity.MONTH: TruncMonth,
        TimeSeriesGranularity.YEAR: TruncYear,
    }
    return trunc_map.get(granularity)


@shared_task
def aggregate_blog_views_hourly():
    """
    Aggregate blog views by hour.
    Runs every hour to aggregate the previous hour's data.
    """
    logger.info("Starting hourly blog views aggregation")
    
    # Get the previous hour's time bucket
    now = timezone.now()
    previous_hour = (now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1))
    
    # Aggregate from raw BlogView data
    aggregates = (
        BlogView.objects
        .filter(viewed_at__gte=previous_hour, viewed_at__lt=previous_hour + timedelta(hours=1))
        .annotate(time_bucket=TruncHour("viewed_at"))
        .values("time_bucket", "blog", "blog__country", "blog__author")
        .annotate(
            view_count=Count("id"),
            unique_blogs_viewed=Count("blog", distinct=True),
            unique_users=Count("user", distinct=True)
        )
    )
    
    created_count = 0
    for agg in aggregates:
        aggregate, _ = BlogViewTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.HOUR,
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
        created_count += 1
    
    # Also create aggregate for all blogs (no filters)
    all_aggregate = (
        BlogView.objects
        .filter(viewed_at__gte=previous_hour, viewed_at__lt=previous_hour + timedelta(hours=1))
        .annotate(time_bucket=TruncHour("viewed_at"))
        .aggregate(
            view_count=Count("id"),
            unique_blogs_viewed=Count("blog", distinct=True),
            unique_users=Count("user", distinct=True)
        )
    )
    
    BlogViewTimeSeriesAggregate.objects.update_or_create(
        granularity=TimeSeriesGranularity.HOUR,
        time_bucket=previous_hour,
        blog=None,
        country=None,
        author=None,
        defaults={
            "view_count": all_aggregate["view_count"],
            "unique_blogs_viewed": all_aggregate["unique_blogs_viewed"],
            "unique_users": all_aggregate["unique_users"],
        }
    )
    created_count += 1
    
    logger.info(f"Completed hourly aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_views_daily():
    """
    Aggregate blog views by day.
    Runs daily to aggregate the previous day's data.
    Can also aggregate from hourly aggregates for efficiency.
    """
    logger.info("Starting daily blog views aggregation")
    
    # Get the previous day's time bucket
    now = timezone.now()
    previous_day = (now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1))
    day_end = previous_day + timedelta(days=1)
    
    # Aggregate from hourly aggregates if available, otherwise from raw data
    hourly_aggregates = BlogViewTimeSeriesAggregate.objects.filter(
        granularity=TimeSeriesGranularity.HOUR,
        time_bucket__gte=previous_day,
        time_bucket__lt=day_end
    )
    
    if hourly_aggregates.exists():
        # Aggregate from hourly aggregates - sum the metrics
        aggregates = (
            hourly_aggregates
            .annotate(time_bucket=TruncDay("time_bucket"))
            .values("time_bucket", "blog", "country", "author")
            .annotate(
                view_count=Sum("view_count"),
                unique_blogs_viewed=Sum("unique_blogs_viewed"),  # Note: This is approximate
                unique_users=Sum("unique_users")  # Note: This is approximate
            )
        )
    else:
        # Fallback to raw data
        aggregates = (
            BlogView.objects
            .filter(viewed_at__gte=previous_day, viewed_at__lt=day_end)
            .annotate(time_bucket=TruncDay("viewed_at"))
            .values("time_bucket", "blog", "blog__country", "blog__author")
            .annotate(
                view_count=Count("id"),
                unique_blogs_viewed=Count("blog", distinct=True),
                unique_users=Count("user", distinct=True)
            )
        )
    
    created_count = 0
    for agg in aggregates:
        BlogViewTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.DAY,
            time_bucket=agg["time_bucket"],
            blog_id=agg.get("blog"),
            country_id=agg.get("country") or agg.get("blog__country"),
            author_id=agg.get("author") or agg.get("blog__author"),
            defaults={
                "view_count": agg["view_count"] or 0,
                "unique_blogs_viewed": agg.get("unique_blogs_viewed", 0),
                "unique_users": agg.get("unique_users", 0),
            }
        )
        created_count += 1
    
    logger.info(f"Completed daily aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_views_weekly():
    """Aggregate blog views by week from daily aggregates."""
    logger.info("Starting weekly blog views aggregation")
    
    now = timezone.now()
    previous_week_start = (now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7))
    week_end = previous_week_start + timedelta(days=7)
    
    # Aggregate from daily aggregates
    daily_aggregates = BlogViewTimeSeriesAggregate.objects.filter(
        granularity=TimeSeriesGranularity.DAY,
        time_bucket__gte=previous_week_start,
        time_bucket__lt=week_end
    )
    
    if not daily_aggregates.exists():
        logger.warning("No daily aggregates found for weekly aggregation")
        return 0
    
    aggregates = (
        daily_aggregates
        .annotate(time_bucket=TruncWeek("time_bucket"))
        .values("time_bucket", "blog", "country", "author")
        .annotate(
            view_count=Sum("view_count"),
            unique_blogs_viewed=Sum("unique_blogs_viewed"),  # Approximate
            unique_users=Sum("unique_users")  # Approximate
        )
    )
    
    created_count = 0
    for agg in aggregates:
        BlogViewTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.WEEK,
            time_bucket=agg["time_bucket"],
            blog_id=agg.get("blog"),
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={
                "view_count": agg["view_count"],
                "unique_blogs_viewed": agg.get("unique_blogs_viewed", 0),
                "unique_users": agg.get("unique_users", 0),
            }
        )
        created_count += 1
    
    logger.info(f"Completed weekly aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_views_monthly():
    """Aggregate blog views by month from daily aggregates."""
    logger.info("Starting monthly blog views aggregation")
    
    now = timezone.now()
    previous_month_start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=32))
    previous_month_start = previous_month_start.replace(day=1)
    
    # Aggregate from daily aggregates
    daily_aggregates = BlogViewTimeSeriesAggregate.objects.filter(
        granularity=TimeSeriesGranularity.DAY,
        time_bucket__gte=previous_month_start,
        time_bucket__lt=previous_month_start + timedelta(days=32)
    )
    
    if not daily_aggregates.exists():
        logger.warning("No daily aggregates found for monthly aggregation")
        return 0
    
    aggregates = (
        daily_aggregates
        .annotate(time_bucket=TruncMonth("time_bucket"))
        .values("time_bucket", "blog", "country", "author")
        .annotate(
            view_count=Sum("view_count"),
            unique_blogs_viewed=Sum("unique_blogs_viewed"),  # Approximate
            unique_users=Sum("unique_users")  # Approximate
        )
    )
    
    created_count = 0
    for agg in aggregates:
        BlogViewTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.MONTH,
            time_bucket=agg["time_bucket"],
            blog_id=agg.get("blog"),
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={
                "view_count": agg["view_count"],
                "unique_blogs_viewed": agg.get("unique_blogs_viewed", 0),
                "unique_users": agg.get("unique_users", 0),
            }
        )
        created_count += 1
    
    logger.info(f"Completed monthly aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_views_yearly():
    """Aggregate blog views by year from monthly aggregates."""
    logger.info("Starting yearly blog views aggregation")
    
    now = timezone.now()
    previous_year_start = (now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365))
    previous_year_start = previous_year_start.replace(month=1, day=1)
    
    # Aggregate from monthly aggregates
    monthly_aggregates = BlogViewTimeSeriesAggregate.objects.filter(
        granularity=TimeSeriesGranularity.MONTH,
        time_bucket__gte=previous_year_start,
        time_bucket__lt=previous_year_start.replace(year=previous_year_start.year + 1)
    )
    
    if not monthly_aggregates.exists():
        logger.warning("No monthly aggregates found for yearly aggregation")
        return 0
    
    aggregates = (
        monthly_aggregates
        .annotate(time_bucket=TruncYear("time_bucket"))
        .values("time_bucket", "blog", "country", "author")
        .annotate(
            view_count=Sum("view_count"),
            unique_blogs_viewed=Sum("unique_blogs_viewed"),  # Approximate
            unique_users=Sum("unique_users")  # Approximate
        )
    )
    
    created_count = 0
    for agg in aggregates:
        BlogViewTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.YEAR,
            time_bucket=agg["time_bucket"],
            blog_id=agg.get("blog"),
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={
                "view_count": agg["view_count"],
                "unique_blogs_viewed": agg.get("unique_blogs_viewed", 0),
                "unique_users": agg.get("unique_users", 0),
            }
        )
        created_count += 1
    
    logger.info(f"Completed yearly aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_creations_daily():
    """Aggregate blog creations by day."""
    logger.info("Starting daily blog creations aggregation")
    
    now = timezone.now()
    previous_day = (now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1))
    day_end = previous_day + timedelta(days=1)
    
    aggregates = (
        Blog.objects
        .filter(created_at__gte=previous_day, created_at__lt=day_end)
        .annotate(time_bucket=TruncDay("created_at"))
        .values("time_bucket", "country", "author")
        .annotate(blog_count=Count("id"))
    )
    
    created_count = 0
    for agg in aggregates:
        BlogCreationTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.DAY,
            time_bucket=agg["time_bucket"],
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={"blog_count": agg["blog_count"]}
        )
        created_count += 1
    
    # All blogs aggregate
    all_count = Blog.objects.filter(
        created_at__gte=previous_day,
        created_at__lt=day_end
    ).count()
    
    BlogCreationTimeSeriesAggregate.objects.update_or_create(
        granularity=TimeSeriesGranularity.DAY,
        time_bucket=previous_day,
        country=None,
        author=None,
        defaults={"blog_count": all_count}
    )
    created_count += 1
    
    logger.info(f"Completed daily blog creations aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_creations_monthly():
    """Aggregate blog creations by month from daily aggregates."""
    logger.info("Starting monthly blog creations aggregation")
    
    now = timezone.now()
    previous_month_start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=32))
    previous_month_start = previous_month_start.replace(day=1)
    
    daily_aggregates = BlogCreationTimeSeriesAggregate.objects.filter(
        granularity=TimeSeriesGranularity.DAY,
        time_bucket__gte=previous_month_start,
        time_bucket__lt=previous_month_start + timedelta(days=32)
    )
    
    if not daily_aggregates.exists():
        logger.warning("No daily aggregates found for monthly blog creation aggregation")
        return 0
    
    aggregates = (
        daily_aggregates
        .annotate(time_bucket=TruncMonth("time_bucket"))
        .values("time_bucket", "country", "author")
        .annotate(blog_count=Sum("blog_count"))
    )
    
    created_count = 0
    for agg in aggregates:
        BlogCreationTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.MONTH,
            time_bucket=agg["time_bucket"],
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={"blog_count": agg["blog_count"]}
        )
        created_count += 1
    
    logger.info(f"Completed monthly blog creations aggregation: {created_count} aggregates created/updated")
    return created_count


@shared_task
def aggregate_blog_creations_yearly():
    """Aggregate blog creations by year from monthly aggregates."""
    logger.info("Starting yearly blog creations aggregation")
    
    now = timezone.now()
    previous_year_start = (now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365))
    previous_year_start = previous_year_start.replace(month=1, day=1)
    
    monthly_aggregates = BlogCreationTimeSeriesAggregate.objects.filter(
        granularity=TimeSeriesGranularity.MONTH,
        time_bucket__gte=previous_year_start,
        time_bucket__lt=previous_year_start.replace(year=previous_year_start.year + 1)
    )
    
    if not monthly_aggregates.exists():
        logger.warning("No monthly aggregates found for yearly blog creation aggregation")
        return 0
    
    aggregates = (
        monthly_aggregates
        .annotate(time_bucket=TruncYear("time_bucket"))
        .values("time_bucket", "country", "author")
        .annotate(blog_count=Sum("blog_count"))
    )
    
    created_count = 0
    for agg in aggregates:
        BlogCreationTimeSeriesAggregate.objects.update_or_create(
            granularity=TimeSeriesGranularity.YEAR,
            time_bucket=agg["time_bucket"],
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={"blog_count": agg["blog_count"]}
        )
        created_count += 1
    
    logger.info(f"Completed yearly blog creations aggregation: {created_count} aggregates created/updated")
    return created_count

