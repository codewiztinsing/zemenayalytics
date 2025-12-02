"""
Service for Performance Analytics business logic using Time Series Aggregates.
"""
from typing import List, Dict, Any, Optional
from django.db.models import Sum, QuerySet
from datetime import datetime

from analytics.models.aggregation import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)
from analytics.utils.helpers import safe_int
from config.logger import logger


class PerformanceAnalyticsService:
    """Service class for performance analytics using time series aggregates."""

    @staticmethod
    def calculate_growth(current: int | float, previous: int | float | None) -> float | None:
        """
        Backwards-compatible single-step growth calculator used by tests.

        Rules (kept exactly as before refactor so tests still pass):
            - previous is None          → None  (first period)
            - previous == 0 and current > 0 → 100.0
            - previous == 0 and current == 0 → None
            - otherwise                 → ((current - previous) / previous) * 100
        """
        if previous is None:
            return None
        if previous == 0:
            if current > 0:
                return 100.0
            return None
        return ((current - previous) / previous) * 100.0

    @staticmethod
    def _compute_growth_series(values: list[int | float]) -> list[float | None]:
        """
        Compute growth percentages from a sequence of values.

        Rules:
            - First period → None
            - previous > 0 → ((current - previous) / previous) * 100
            - previous == 0 and current > 0 → 100
            - previous == 0 and current == 0 → None
        """
        growth: list[float | None] = []
        prev: int | float | None = None

        for current in values:
            growth.append(PerformanceAnalyticsService.calculate_growth(current, prev))
            prev = current

        return growth

    @staticmethod
    def _parse_iso_date(date_str: str) -> datetime:
        """Parse ISO date string with optional 'Z'."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO date: {date_str}")

    @staticmethod
    def _apply_filters(
        qs: QuerySet,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> QuerySet:
        """Apply dynamic filters, user filter, and date range to a queryset."""
        if filters:
            if "blog" in filters:
                qs = qs.filter(blog_id=safe_int(filters["blog"]))
            if "country" in filters:
                qs = qs.filter(country_id=safe_int(filters["country"]))
            if "author" in filters:
                qs = qs.filter(author_id=safe_int(filters["author"]))

        if user_id is not None:
            qs = qs.filter(author_id=user_id)

        if start:
            qs = qs.filter(time_bucket__gte=PerformanceAnalyticsService._parse_iso_date(start))
        if end:
            qs = qs.filter(time_bucket__lte=PerformanceAnalyticsService._parse_iso_date(end))

        return qs

    @staticmethod
    def get_performance_analytics(
        compare: str = "month",
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance analytics using time series aggregates.

        Returns a list of dictionaries with:
            x → period label + blog count
            y → total views
            z → growth percentage
        """
        # Map compare to granularity enum
        granularity_map = {
            "day": TimeSeriesGranularity.DAY,
            "week": TimeSeriesGranularity.WEEK,
            "month": TimeSeriesGranularity.MONTH,
            "year": TimeSeriesGranularity.YEAR,
        }

        if compare not in granularity_map:
            raise ValueError(f"Invalid compare value: {compare}. Must be one of {list(granularity_map.keys())}")

        granularity = granularity_map[compare]

        # Base querysets
        view_qs = BlogViewTimeSeriesAggregate.objects.filter(granularity=granularity)
        blog_qs = BlogCreationTimeSeriesAggregate.objects.filter(granularity=granularity)

        # Apply filters
        view_qs = PerformanceAnalyticsService._apply_filters(view_qs, filters, user_id, start, end)
        blog_qs = PerformanceAnalyticsService._apply_filters(blog_qs, filters, user_id, start, end)

        # Aggregate by time_bucket
        view_data = (
            view_qs.values("time_bucket")
            .annotate(total_views=Sum("view_count"))
            .order_by("time_bucket")
        )
        blog_data = (
            blog_qs.values("time_bucket")
            .annotate(total_blogs=Sum("blog_count"))
            .order_by("time_bucket")
        )

        # Map blog counts by time_bucket for quick lookup
        blog_counts = {item["time_bucket"]: item["total_blogs"] for item in blog_data}

        # Build rows
        rows: List[Dict[str, Any]] = []
        for item in view_data:
            time_bucket = item["time_bucket"]
            views = item["total_views"]
            blog_count = blog_counts.get(time_bucket, 0)
            period_label = time_bucket.strftime("%Y-%m-%d")
            x_label = f"{period_label} ({blog_count} blogs)"
            rows.append({"x": x_label, "y": views})

        # Compute growth percentage series
        views_series = [row["y"] for row in rows]
        growth_series = PerformanceAnalyticsService._compute_growth_series(views_series)

        for row, growth in zip(rows, growth_series):
            row["z"] = growth

        return rows
