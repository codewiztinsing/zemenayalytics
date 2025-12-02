"""
Service for Performance Analytics business logic using Time Series Aggregates.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from django.db.models import Sum, QuerySet
from datetime import datetime
from django.db.models import Model


from analytics.models.aggregation import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)
from analytics.utils.helpers import safe_int
from config.logger import logger


class PerformanceAnalyticsService:
    """Service class for performance analytics using time series aggregates."""

    # ----------------------------------------------------------------------
    # Growth % calculation 
    # ----------------------------------------------------------------------


    @staticmethod
    def _base_queryset(model: Model, granularity: str) -> QuerySet:
        qs = model.objects.filter(granularity=granularity).select_related("blog", "author", "country")
        return qs


    @staticmethod
    def _growth(prev: float | int | None, curr: float | int) -> float | None:
        """
        Compute growth percentage for a single step.

        Rules:
            - prev is None                → None
            - prev == 0 and curr > 0      → 100.0
            - prev == 0 and curr == 0     → None
            - otherwise                   → ((curr - prev) / prev) * 100
        """
        if prev is None:
            return None
        if prev == 0:
            return 100.0 if curr > 0 else None
        return ((curr - prev) / prev) * 100.0

    # Backwards‑compatible public helper expected by tests
    @staticmethod
    def calculate_growth(current: float | int | None, previous: float | int | None) -> float | None:

        return PerformanceAnalyticsService._growth(previous, current if current is not None else 0)

    @staticmethod
    def _compute_growth_series(values: list[int | float]) -> list[float | None]:
        """
        Compute growth percentages for an entire list of values.
        """
        growth_list: list[float | None] = []
        prev: float | int | None = None

        for curr in values:
            growth_list.append(PerformanceAnalyticsService._growth(prev, curr))
            prev = curr

        return growth_list

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    @staticmethod
    def _parse_iso_date(date_str: str) -> datetime:
        """Parse ISO date strings safely, including optional 'Z' UTC suffix."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO date: {date_str}")


    @staticmethod
    def _build_result_rows(view_data: QuerySet, blog_counts: Dict[datetime, int]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for item in view_data:
            bucket = item["time_bucket"]
            views = item["total_views"]
            blog_count = blog_counts.get(bucket, 0)

            # Format label
            bucket_label = bucket.strftime("%Y-%m-%d")
            x_label = f"{bucket_label} ({blog_count} blogs)"

            rows.append({"x": x_label, "y": views})

        # Growth calculation (clean new version)
        values = [row["y"] for row in rows]
        growth_values = PerformanceAnalyticsService._compute_growth_series(values)

        if growth_values:
            growth_values[0] = 0.0

        for row, growth in zip(rows, growth_values):
            row["z"] = growth
        return rows

    @staticmethod
    def _apply_filters(
        qs: QuerySet,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> QuerySet:
        """
        Apply dynamic filters + author filter + date range.
        """

        # Dynamic filters
        if filters:
            if "blog" in filters:
                qs = qs.filter(blog_id=safe_int(filters["blog"]))
            if "country" in filters:
                qs = qs.filter(country_id=safe_int(filters["country"]))
            if "author" in filters:
                qs = qs.filter(author_id=safe_int(filters["author"]))

        # Author filter
        if user_id is not None:
            qs = qs.filter(author_id=user_id)

        # Time range filtering
        if start:
            qs = qs.filter(time_bucket__gte=PerformanceAnalyticsService._parse_iso_date(start))
        if end:
            qs = qs.filter(time_bucket__lte=PerformanceAnalyticsService._parse_iso_date(end))

        return qs

    # ----------------------------------------------------------------------
    # Main API
    # ----------------------------------------------------------------------
    @staticmethod
    def get_performance_analytics(
        compare: str = "month",
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance analytics using time-series aggregate tables.

        Returns rows:
            x → label (period + blog count)
            y → total views
            z → growth percentage
        """

        # Supported granularities
        granularity_map = {
            "day": TimeSeriesGranularity.DAY,
            "week": TimeSeriesGranularity.WEEK,
            "month": TimeSeriesGranularity.MONTH,
            "year": TimeSeriesGranularity.YEAR,
        }

        if compare not in granularity_map:
            raise ValueError(f"Invalid compare '{compare}'. Choose from {list(granularity_map.keys())}")

        granularity = granularity_map[compare]

        # Base aggregated views queryset
        view_qs = BlogViewTimeSeriesAggregate.objects.filter(granularity=granularity)
        blog_qs = BlogCreationTimeSeriesAggregate.objects.filter(granularity=granularity)

        # Apply filters
        view_qs = PerformanceAnalyticsService._base_queryset(BlogViewTimeSeriesAggregate, granularity)
        blog_qs = PerformanceAnalyticsService._base_queryset(BlogCreationTimeSeriesAggregate, granularity)

        logger.debug(f"View queryset: {view_qs.count()}")
        logger.debug(f"Blog queryset: {blog_qs.count()}")

        # Aggregate view counts by time period
        view_data = (
            view_qs.values("time_bucket")
            .annotate(total_views=Sum("view_count"))
            .order_by("time_bucket")
        )

        # Aggregate blog creation counts by time period
        blog_data = (
            blog_qs.values("time_bucket")
            .annotate(total_blogs=Sum("blog_count"))
            .order_by("time_bucket")
        )


        logger.debug(f"View data: {view_data.count()}")
        logger.debug(f"Blog data: {blog_data.count()}")

        # Fast lookup dictionary
        blog_counts = {
            row["time_bucket"]: row["total_blogs"]
            for row in blog_data
        }

        # Build result rows
        rows = PerformanceAnalyticsService._build_result_rows(view_data, blog_counts)
        logger.debug(f"Rows: {rows}")
        return rows
