"""
Analytics app views.

Each view is defined in its own module for better organization.
"""
from apps.analytics.views.blog_views_analytics import BlogViewsAnalyticsView
from apps.analytics.views.top_analytics import TopAnalyticsView
from apps.analytics.views.performance_analytics import PerformanceAnalyticsView

__all__ = [
    "BlogViewsAnalyticsView",
    "TopAnalyticsView",
    "PerformanceAnalyticsView",
]

