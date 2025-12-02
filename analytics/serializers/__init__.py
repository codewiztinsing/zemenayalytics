"""
Analytics app serializers.

Each serializer is defined in its own module for better organization.
"""
from analytics.serializers.blog_serializers import (
    BlogViewsAnalyticsRequestSerializer,
    BlogViewsAnalyticsResponseSerializer,
)
from analytics.serializers.top_serializers import (
    TopAnalyticsRequestSerializer,
    TopAnalyticsResponseSerializer,
)
from analytics.serializers.performance_serializers import (
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

