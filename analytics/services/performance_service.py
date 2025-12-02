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
        
        # Build result with growth calculation
        result = []
        previous_views = None
        
        for item in view_data:
            time_bucket = item["time_bucket"]
            views = item["total_views"]
            blog_count = blog_counts.get(time_bucket, 0)
            
            # Calculate growth percentage
            growth_pct = None
            if previous_views is not None and previous_views > 0:
                growth_pct = ((views - previous_views) / previous_views) * 100
            elif previous_views == 0 and views > 0:
                growth_pct = 100.0
            
            # Format period label
            period_label = time_bucket.strftime("%Y-%m-%d")
            x_label = f"{period_label} ({blog_count} blogs)"
            
            result.append({
                "x": x_label,
                "y": views,
                "z": growth_pct,
            })
            
            previous_views = views
        
        return result

