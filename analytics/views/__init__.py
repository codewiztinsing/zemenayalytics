"""
Analytics app views.

Each view is defined in its own module for better organization.
"""
from analytics.views.blog_views import BlogViewsAnalyticsView
from analytics.views.top_views import TopAnalyticsView
from analytics.views.performance_views import PerformanceAnalyticsView

__all__ = [
    "BlogViewsAnalyticsView",
    "TopAnalyticsView",
    "PerformanceAnalyticsView",
]

