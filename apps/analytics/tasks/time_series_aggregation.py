"""
Backward-compatibility shim for legacy Celery task paths.

Older Celery beat schedules may still reference tasks using the
``apps.analytics.tasks.time_series_aggregation`` module, e.g.::

    apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_hourly

The real implementations now live in ``analytics.tasks.aggregation``.
This module defines *alias tasks* with the old names that simply
delegate to the new implementations, so existing schedules continue
to work without migration.
"""

from celery import shared_task

from analytics.tasks import aggregation as _aggregation


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_hourly"
)
def aggregate_blog_views_hourly(*args, **kwargs):
    return _aggregation.aggregate_blog_views_hourly(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_daily"
)
def aggregate_blog_views_daily(*args, **kwargs):
    return _aggregation.aggregate_blog_views_daily(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_weekly"
)
def aggregate_blog_views_weekly(*args, **kwargs):
    return _aggregation.aggregate_blog_views_weekly(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_monthly"
)
def aggregate_blog_views_monthly(*args, **kwargs):
    return _aggregation.aggregate_blog_views_monthly(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_yearly"
)
def aggregate_blog_views_yearly(*args, **kwargs):
    return _aggregation.aggregate_blog_views_yearly(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_creations_daily"
)
def aggregate_blog_creations_daily(*args, **kwargs):
    return _aggregation.aggregate_blog_creations_daily(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_creations_monthly"
)
def aggregate_blog_creations_monthly(*args, **kwargs):
    return _aggregation.aggregate_blog_creations_monthly(*args, **kwargs)


@shared_task(
    name="apps.analytics.tasks.time_series_aggregation.aggregate_blog_creations_yearly"
)
def aggregate_blog_creations_yearly(*args, **kwargs):
    return _aggregation.aggregate_blog_creations_yearly(*args, **kwargs)


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



