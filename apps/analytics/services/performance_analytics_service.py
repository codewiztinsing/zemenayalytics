"""
Service for Performance Analytics business logic using Time Series Aggregates.
"""
from typing import List, Dict, Any
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime

from apps.analytics.models.time_series_aggregate import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)
from apps.analytics.utils.helpers import safe_int
from config.logger import logger


class PerformanceAnalyticsService:
    """Service class for performance analytics business logic using time series aggregates."""

    # Map compare parameter to granularity
    GRANULARITY_MAP = {
        "day": TimeSeriesGranularity.DAY,
        "week": TimeSeriesGranularity.WEEK,
        "month": TimeSeriesGranularity.MONTH,
        "year": TimeSeriesGranularity.YEAR,
    }

    @staticmethod
    def calculate_growth(views: int, prev_views: int | None) -> float | None:
        """
        Calculate growth percentage compared to previous period.
        
        Args:
            views: Current period views
            prev_views: Previous period views (None for first period)
        
        Returns:
            Growth percentage or None if not calculable
        """
        if prev_views is None:
            return None
        
        if prev_views == 0:
            return None if views == 0 else 100.0
        
        return (views - prev_views) / prev_views * 100.0

    @staticmethod
    def _map_filter_field_to_aggregate_field(field: str) -> str | None:
        """
        Map filter field paths to aggregate model field paths.
        Returns None if field cannot be mapped to aggregate fields.
        """
        # Map common filter fields to aggregate model fields
        field_mapping = {
            "blog.country.code": "country__code",
            "country.code": "country__code",
            "blog.country.id": "country_id",
            "country.id": "country_id",
            "blog.author.id": "author_id",
            "author.id": "author_id",
            "blog.author.user.id": "author__user_id",
            "author.user.id": "author__user_id",
        }
        return field_mapping.get(field)

    @staticmethod
    def _build_filter_q_from_dict(filter_obj: Dict[str, Any]) -> Q:
        """
        Recursively build Q object from filter dict for aggregate models.
        Only processes filters that can be mapped to aggregate fields.
        """
        if not isinstance(filter_obj, dict):
            return Q()

        q = Q()

        # Handle logical combinators
        if "and" in filter_obj:
            children = filter_obj["and"]
            if isinstance(children, list):
                for child in children:
                    child_q = PerformanceAnalyticsService._build_filter_q_from_dict(child)
                    if child_q:
                        q &= child_q

        if "or" in filter_obj:
            children = filter_obj["or"]
            if isinstance(children, list):
                or_q = Q()
                for child in children:
                    child_q = PerformanceAnalyticsService._build_filter_q_from_dict(child)
                    if child_q:
                        or_q |= child_q
                if or_q:
                    q &= or_q

        if "not" in filter_obj:
            child_q = PerformanceAnalyticsService._build_filter_q_from_dict(filter_obj["not"])
            if child_q:
                q &= ~child_q

        # Handle comparison operators
        for op in ("eq", "in", "lt", "lte", "gt", "gte", "contains"):
            if op in filter_obj:
                payload = filter_obj[op]
                if not isinstance(payload, dict):
                    continue
                
                field = payload.get("field")
                value = payload.get("value")
                
                if not field:
                    continue
                
                # Map field to aggregate field
                aggregate_field = PerformanceAnalyticsService._map_filter_field_to_aggregate_field(field)
                if not aggregate_field:
                    # Skip filters that can't be mapped to aggregate fields
                    logger.debug(f"Skipping filter field '{field}' - cannot map to aggregate model")
                    continue
                
                # Build lookup based on operator
                if op == "eq":
                    q &= Q(**{aggregate_field: value})
                elif op == "in":
                    if isinstance(value, list):
                        q &= Q(**{f"{aggregate_field}__in": value})
                elif op == "contains":
                    q &= Q(**{f"{aggregate_field}__icontains": value})
                else:  # lt, lte, gt, gte
                    q &= Q(**{f"{aggregate_field}__{op}": value})

        return q

    @staticmethod
    def _apply_filters_to_aggregates(
        filters: Dict[str, Any] | None = None,
        user_id: int | None = None,
    ) -> Q:
        """
        Build Q object for filtering aggregate querysets.
        Filters are applied to foreign key relationships in aggregates.
        """
        q = Q()
        
        # User filter (maps to author)
        if user_id:
            q &= Q(author_id=user_id)
        
        # Apply dynamic filters
        if filters:
            filter_q = PerformanceAnalyticsService._build_filter_q_from_dict(filters)
            if filter_q:
                q &= filter_q
        
        return q

    @staticmethod
    def get_performance_analytics(
        compare: str,
        filters: Dict[str, Any] | None = None,
        user_id: int | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance analytics over time periods with growth metrics using time series aggregates.
        
        Shows time-series performance for a user or all users.
        
        Args:
            compare: Period size ('month', 'week', 'day', 'year')
            filters: Dynamic filter tree (applied to aggregate foreign keys)
            user_id: Optional user ID to filter by (maps to author). If None, shows all users.
            start: Start date in ISO format
            end: End date in ISO format
        
        Returns:
            List of dictionaries with:
            - x: Period label + number_of_blogs created (e.g., "2025-01-15 (5 blogs)")
            - y: Views during the period
            - z: Growth/decline percentage vs previous period (None for first period)
        """
        if compare not in PerformanceAnalyticsService.GRANULARITY_MAP:
            raise ValueError(
                f"Invalid compare value: {compare}. Must be one of {list(PerformanceAnalyticsService.GRANULARITY_MAP.keys())}"
            )

        granularity = PerformanceAnalyticsService.GRANULARITY_MAP[compare]
        logger.info(f"Fetching performance analytics with granularity: {granularity}, compare: {compare}")

        # Build filter Q object
        filter_q = PerformanceAnalyticsService._apply_filters_to_aggregates(
            filters=filters, user_id=user_id
        )

        logger.info(f"Filter Q: {filter_q}")

        # Query view aggregates
        # If no filters, use "all" aggregates (blog=null, country=null, author=null)
        # If filters exist, use aggregates matching those filters
        view_qs = BlogViewTimeSeriesAggregate.objects.filter(
            granularity=granularity
        )

        logger.info(f"View Q Count: {view_qs.count()}")
        if filter_q:
            # Apply filters - get aggregates matching the filter criteria
            view_qs = view_qs.filter(filter_q)
        else:
            # No filters: use "all" aggregates (where all foreign keys are null)
            view_qs = view_qs.filter(blog__isnull=True, country__isnull=True, author__isnull=True)
        
        # Apply time range filters
        if start:
            view_qs = view_qs.filter(time_bucket__gte=start)
        if end:
            view_qs = view_qs.filter(time_bucket__lte=end)

        # Aggregate views by period (time_bucket)
        # Group by time_bucket and sum view_count
        view_agg = (
            view_qs
            .values("time_bucket")
            .annotate(views_in_period=Sum("view_count"))
            .order_by("time_bucket")
        )

        # Query blog creation aggregates
        blog_qs = BlogCreationTimeSeriesAggregate.objects.filter(
            granularity=granularity
        )
        
        if filter_q:
            # Apply filters - get aggregates matching the filter criteria
            blog_qs = blog_qs.filter(filter_q)
        else:
            # No filters: use "all" aggregates (where all foreign keys are null)
            blog_qs = blog_qs.filter(country__isnull=True, author__isnull=True)
        
        # Apply time range filters
        if start:
            blog_qs = blog_qs.filter(time_bucket__gte=start)
        if end:
            blog_qs = blog_qs.filter(time_bucket__lte=end)

        # Aggregate blog counts by period
        blog_agg = (
            blog_qs
            .values("time_bucket")
            .annotate(blogs_in_period=Sum("blog_count"))
            .order_by("time_bucket")
        )

        # Convert to dict for quick lookup
        views_map = {row["time_bucket"]: row["views_in_period"] for row in view_agg}
        blogs_map = {row["time_bucket"]: row["blogs_in_period"] for row in blog_agg}

        # Build sorted list of periods (union of periods)
        all_periods = sorted(set(views_map.keys()) | set(blogs_map.keys()))

        # Compute growth vs previous period
        result: List[Dict[str, Any]] = []
        prev_views = None
        for period in all_periods:
            views = safe_int(views_map.get(period, 0))
            blogs_count = safe_int(blogs_map.get(period, 0))
            
            growth = PerformanceAnalyticsService.calculate_growth(views, prev_views)
            prev_views = views

            # Format period label based on granularity
            # x = period label + number_of_blogs created
            if isinstance(period, datetime):
                # Format based on compare granularity for better readability
                if compare == "day":
                    label = f"{period.strftime('%Y-%m-%d')} ({blogs_count} blogs)"
                elif compare == "week":
                    # ISO week format: YYYY-Www
                    year, week, _ = period.isocalendar()
                    label = f"{year}-W{week:02d} ({blogs_count} blogs)"
                elif compare == "month":
                    label = f"{period.strftime('%Y-%m')} ({blogs_count} blogs)"
                elif compare == "year":
                    label = f"{period.strftime('%Y')} ({blogs_count} blogs)"
                else:
                    label = f"{period.isoformat()} ({blogs_count} blogs)"
            else:
                label = f"{period} ({blogs_count} blogs)"
            
            result.append({
                "x": label,  # Period label + number_of_blogs created
                "y": views,  # Views during the period
                "z": (round(growth, 2) if growth is not None else None)  # Growth/decline percentage vs previous period
            })

        logger.info(f"Retrieved {len(result)} performance analytics periods")
        return result
