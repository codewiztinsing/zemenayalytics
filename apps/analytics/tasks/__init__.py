"""
Compat tasks package for the legacy ``apps.analytics.tasks`` path.

Celery beat in existing environments may still refer to tasks using
the old dotted path, e.g.::

    apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_hourly

This package re-exports the new task implementations so those
scheduled tasks keep working.
"""

from .time_series_aggregation import (  # noqa: F401
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


