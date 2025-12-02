"""
Celery tasks for analytics app.
"""
from .aggregation import (
    aggregate_blog_views_hourly,
    aggregate_blog_views_daily,
    aggregate_blog_views_weekly,
    aggregate_blog_views_monthly,
    aggregate_blog_views_yearly,
    aggregate_blog_creations_daily,
    aggregate_blog_creations_monthly,
    aggregate_blog_creations_yearly,
)

__all__ = [
    "aggregate_blog_views_hourly",
    "aggregate_blog_views_daily",
    "aggregate_blog_views_weekly",
    "aggregate_blog_views_monthly",
    "aggregate_blog_views_yearly",
    "aggregate_blog_creations_daily",
    "aggregate_blog_creations_monthly",
    "aggregate_blog_creations_yearly",
]

