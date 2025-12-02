"""
Celery tasks for time series aggregation.

These tasks aggregate BlogView and Blog data at different granularities
and store them in the time series aggregate tables.
"""
from datetime import timedelta

from celery import shared_task
from django.db.models import Count, Sum
from django.db.models.functions import (
    TruncDay,
    TruncHour,
    TruncMonth,
    TruncWeek,
    TruncYear,
)
from django.utils import timezone

from config.logger import logger

from analytics.models import BlogView, Blog
from analytics.models.aggregation import (
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


def _get_period_bounds(granularity: str) -> tuple:
    """
    Compute [start, end) bounds for the *previous* period of the given granularity.
    """
    now = timezone.now()

    if granularity == TimeSeriesGranularity.HOUR:
        end = now.replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=1)
    elif granularity == TimeSeriesGranularity.DAY:
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=1)
    elif granularity == TimeSeriesGranularity.WEEK:
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=7)
    elif granularity == TimeSeriesGranularity.MONTH:
        # Start of current month
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Start of previous month
        end = current_month_start
        start = (current_month_start - timedelta(days=1)).replace(day=1)
    elif granularity == TimeSeriesGranularity.YEAR:
        # Start of current year
        current_year_start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Start of previous year
        end = current_year_start
        start = current_year_start.replace(year=current_year_start.year - 1)
    else:
        raise ValueError(f"Unsupported granularity: {granularity}")

    return start, end


def _aggregate_blog_views(granularity: str) -> int:
    """
    Generic aggregator for BlogView → BlogViewTimeSeriesAggregate.

    Used by Celery tasks for hourly/daily/weekly/monthly/yearly aggregations.
    """
    logger.info(f"Starting {granularity} blog views aggregation")

    trunc_func = get_time_trunc_func(granularity)
    if trunc_func is None:
        raise ValueError(f"No truncation function for granularity: {granularity}")

    start, end = _get_period_bounds(granularity)

    aggregates = (
        BlogView.objects.filter(viewed_at__gte=start, viewed_at__lt=end)
        .annotate(time_bucket=trunc_func("viewed_at"))
        .values("time_bucket", "blog", "blog__country", "blog__author")
        .annotate(
            view_count=Count("id"),
            unique_blogs_viewed=Count("blog", distinct=True),
            unique_users=Count("user", distinct=True),
        )
    )

    created_count = 0
    for agg in aggregates:
        BlogViewTimeSeriesAggregate.objects.update_or_create(
            granularity=granularity,
            time_bucket=agg["time_bucket"],
            blog_id=agg["blog"],
            country_id=agg["blog__country"],
            author_id=agg["blog__author"],
            defaults={
                "view_count": agg["view_count"],
                "unique_blogs_viewed": agg["unique_blogs_viewed"],
                "unique_users": agg["unique_users"],
            },
        )
        created_count += 1

    logger.info(
        f"Completed {granularity} blog views aggregation: "
        f"{created_count} aggregates created/updated"
    )
    return created_count


def _aggregate_blog_creations(granularity: str) -> int:
    """
    Generic aggregator for Blog → BlogCreationTimeSeriesAggregate.

    Used by Celery tasks for daily/monthly/yearly aggregations.
    """
    logger.info(f"Starting {granularity} blog creations aggregation")

    trunc_func = get_time_trunc_func(granularity)
    if trunc_func is None:
        raise ValueError(f"No truncation function for granularity: {granularity}")

    start, end = _get_period_bounds(granularity)

    aggregates = (
        Blog.objects.filter(created_at__gte=start, created_at__lt=end)
        .annotate(time_bucket=trunc_func("created_at"))
        .values("time_bucket", "country", "author")
        .annotate(blog_count=Count("id"))
    )

    created_count = 0
    for agg in aggregates:
        BlogCreationTimeSeriesAggregate.objects.update_or_create(
            granularity=granularity,
            time_bucket=agg["time_bucket"],
            country_id=agg.get("country"),
            author_id=agg.get("author"),
            defaults={"blog_count": agg["blog_count"]},
        )
        created_count += 1

    logger.info(
        f"Completed {granularity} blog creations aggregation: "
        f"{created_count} aggregates created/updated"
    )
    return created_count


@shared_task
def aggregate_blog_views_hourly():
    """Aggregate blog views by hour for the previous hour."""
    return _aggregate_blog_views(TimeSeriesGranularity.HOUR)


@shared_task
def aggregate_blog_views_daily():
    """
    Aggregate blog views by day.
    Runs daily to aggregate the previous day's data.
    Can also aggregate from hourly aggregates for efficiency.
    """
    """Aggregate blog views by day for the previous day."""
    return _aggregate_blog_views(TimeSeriesGranularity.DAY)


@shared_task
def aggregate_blog_views_weekly():
    """Aggregate blog views by week for the previous week."""
    return _aggregate_blog_views(TimeSeriesGranularity.WEEK)


@shared_task
def aggregate_blog_views_monthly():
    """Aggregate blog views by month for the previous month."""
    return _aggregate_blog_views(TimeSeriesGranularity.MONTH)


@shared_task
def aggregate_blog_views_yearly():
    """Aggregate blog views by year for the previous year."""
    return _aggregate_blog_views(TimeSeriesGranularity.YEAR)


@shared_task
def aggregate_blog_creations_daily():
    """Aggregate blog creations by day for the previous day."""
    return _aggregate_blog_creations(TimeSeriesGranularity.DAY)


@shared_task
def aggregate_blog_creations_monthly():
    """Aggregate blog creations by month for the previous month."""
    return _aggregate_blog_creations(TimeSeriesGranularity.MONTH)


@shared_task
def aggregate_blog_creations_yearly():
    """Aggregate blog creations by year for the previous year."""
    return _aggregate_blog_creations(TimeSeriesGranularity.YEAR)

