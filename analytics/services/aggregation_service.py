"""
Service for Time Series Analytics business logic.
"""
from typing import List, Dict, Any
from django.db.models import Count
from django.db.models.functions import TruncDate
from analytics.models import BlogView
from analytics.utils.filters import build_q_from_filter
from analytics.utils.helpers import parse_timerange, TRUNC_MAP


class TimeSeriesService:
    """Service class for time series analytics business logic."""

    @staticmethod
    def get_time_series(
        granularity: str = "day",
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get time series data for blog views aggregated by time period.
        
        Args:
            granularity: Time granularity ('day', 'week', 'month', 'year')
            filters: Dynamic filter tree
            start: Start date in ISO format (YYYY-MM-DD)
            end: End date in ISO format (YYYY-MM-DD)
        
        Returns:
            List of dictionaries with x (time period), y (view count), z (unique blogs viewed)
        """
        if granularity not in TRUNC_MAP:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(TRUNC_MAP.keys())}")
        
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")
        
        # Apply dynamic filters if provided
        if filters:
            q = build_q_from_filter(filters)
            view_qs = view_qs.filter(q)
        
        # Apply time range to the view timestamp
        # Apply time range based on created_at (from BaseModel)
        view_qs = parse_timerange(view_qs, start, end, datetime_field="created_at")
        
        # Get truncation function for the specified granularity
        trunc_func = TRUNC_MAP[granularity]
        
        # Aggregate views by time period
        agg_qs = (
            view_qs
            .annotate(period=trunc_func("viewed_at"))
            .values("period")
            .annotate(
                view_count=Count("id"),
                unique_blogs=Count("blog", distinct=True)
            )
            .order_by("period")
        )
        
        # Map to expected x,y,z format
        result = [
            {
                "x": row["period"].isoformat() if hasattr(row["period"], "isoformat") else str(row["period"]),
                "y": row["view_count"],
                "z": row["unique_blogs"]
            }
            for row in agg_qs
        ]
        
        return result

