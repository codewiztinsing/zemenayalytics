"""
Analytics app serializers.

Each serializer is defined in its own module for better organization.
"""
from apps.analytics.serializers.blog_views_analytics import (
    BlogViewsAnalyticsRequestSerializer,
    BlogViewsAnalyticsResponseSerializer,
)
from apps.analytics.serializers.top_analytics import (
    TopAnalyticsRequestSerializer,
    TopAnalyticsResponseSerializer,
)
from apps.analytics.serializers.performance_analytics import (
    PerformanceAnalyticsRequestSerializer,
    PerformanceAnalyticsResponseSerializer,
)

__all__ = [
    "BlogViewsAnalyticsRequestSerializer",
    "BlogViewsAnalyticsResponseSerializer",
    "TopAnalyticsRequestSerializer",
    "TopAnalyticsResponseSerializer",
    "PerformanceAnalyticsRequestSerializer",
    "PerformanceAnalyticsResponseSerializer",
]

