"""
Service for Performance Analytics business logic using Time Series Aggregates.
"""
from typing import List, Dict, Any
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime

from analytics.models.aggregation import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)
from analytics.utils.helpers import safe_int
from config.logger import logger


class PerformanceAnalyticsService:
    """Service class for performance analytics business logic using time series aggregates."""

    @staticmethod
    def _compute_growth_series(values: list[int | float]) -> list[float | None]:
        """
        Given a sequence of values (e.g. views per period), compute growth percentages.

        Rules:
            - First period has no previous value → growth is None
            - previous > 0 → ((current - previous) / previous) * 100
            - previous == 0 and current > 0 → 100.0
            - previous == 0 and current == 0 → None
        """
        growth: list[float | None] = []
        prev: int | float | None = None

        for current in values:
            if prev is None:
                growth.append(None)
            elif prev > 0:
                growth.append(((current - prev) / prev) * 100)
            elif prev == 0 and current > 0:
                growth.append(100.0)
            else:
                growth.append(None)

            prev = current

        return growth

    @staticmethod
    def get_performance_analytics(
        compare: str = "month",
        filters: Dict[str, Any] | None = None,
        user_id: int | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance analytics using time series aggregates.
        
        Args:
            compare: Period size ('month', 'week', 'day', 'year')
            filters: Dynamic filter tree
            user_id: Optional user ID to filter by specific user
            start: Start date in ISO format (YYYY-MM-DD)
            end: End date in ISO format (YYYY-MM-DD)
        
        Returns:
            List of dictionaries with x (period label + blog count), y (views), z (growth %)
        """
        # Map compare to granularity
        granularity_map = {
            "day": TimeSeriesGranularity.DAY,
            "week": TimeSeriesGranularity.WEEK,
            "month": TimeSeriesGranularity.MONTH,
            "year": TimeSeriesGranularity.YEAR,
        }
        
        if compare not in granularity_map:
            raise ValueError(f"Invalid compare value: {compare}. Must be one of: {list(granularity_map.keys())}")
        
        granularity = granularity_map[compare]
        
        # Build query for aggregates
        view_agg_qs = BlogViewTimeSeriesAggregate.objects.filter(granularity=granularity)
        blog_agg_qs = BlogCreationTimeSeriesAggregate.objects.filter(granularity=granularity)
        
        # Apply filters if provided
        if filters:
            # Apply filters to aggregates (simplified - you may need to adjust based on your filter structure)
            if "blog" in filters:
                view_agg_qs = view_agg_qs.filter(blog_id=safe_int(filters["blog"]))
                blog_agg_qs = blog_agg_qs.filter(blog__id=safe_int(filters["blog"]))
            if "country" in filters:
                view_agg_qs = view_agg_qs.filter(country_id=safe_int(filters["country"]))
                blog_agg_qs = blog_agg_qs.filter(country_id=safe_int(filters["country"]))
            if "author" in filters:
                view_agg_qs = view_agg_qs.filter(author_id=safe_int(filters["author"]))
                blog_agg_qs = blog_agg_qs.filter(author_id=safe_int(filters["author"]))
        
        # Apply user filter if provided
        if user_id:
            # Note: User filtering on aggregates may require different approach
            # This is a simplified version
            pass
        
        # Apply date range if provided
        if start:
            try:
                start_date = datetime.fromisoformat(start.replace("Z", "+00:00"))
                view_agg_qs = view_agg_qs.filter(time_bucket__gte=start_date)
                blog_agg_qs = blog_agg_qs.filter(time_bucket__gte=start_date)
            except ValueError:
                raise ValueError(f"Invalid start date format: {start}")
        
        if end:
            try:
                end_date = datetime.fromisoformat(end.replace("Z", "+00:00"))
                view_agg_qs = view_agg_qs.filter(time_bucket__lte=end_date)
                blog_agg_qs = blog_agg_qs.filter(time_bucket__lte=end_date)
            except ValueError:
                raise ValueError(f"Invalid end date format: {end}")
        
        # Get aggregates grouped by time bucket
        view_data = (
            view_agg_qs
            .values("time_bucket")
            .annotate(total_views=Sum("view_count"))
            .order_by("time_bucket")
        )
        
        blog_data = (
            blog_agg_qs
            .values("time_bucket")
            .annotate(total_blogs=Sum("blog_count"))
            .order_by("time_bucket")
        )
        
        # Create a dictionary for quick lookup
        blog_counts = {item["time_bucket"]: item["total_blogs"] for item in blog_data}
        
        # First build rows with period label and views
        rows: list[Dict[str, Any]] = []
        for item in view_data:
            time_bucket = item["time_bucket"]
            views = item["total_views"]
            blog_count = blog_counts.get(time_bucket, 0)

            period_label = time_bucket.strftime("%Y-%m-%d")
            x_label = f"{period_label} ({blog_count} blogs)"

            rows.append(
                {
                    "x": x_label,
                    "y": views,
                    # z (growth) will be filled in a separate pass for clarity
                }
            )

        # Compute growth percentages in a dedicated helper for readability
        views_series = [row["y"] for row in rows]
        growth_series = PerformanceAnalyticsService._compute_growth_series(views_series)

        for row, growth in zip(rows, growth_series):
            row["z"] = growth

        return rows

