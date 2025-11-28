"""
Analytics API v1 URL configuration.
"""
from django.urls import path
from apps.analytics.views import (
    BlogViewsAnalyticsView,
    TopAnalyticsView,
    PerformanceAnalyticsView,
)

app_name = "analytics_v1"

urlpatterns = [
    path("blog-views/", BlogViewsAnalyticsView.as_view(), name="blog-views-analytics"),
    path("top/", TopAnalyticsView.as_view(), name="top-analytics"),
    path("performance/", PerformanceAnalyticsView.as_view(), name="performance-analytics"),
]

