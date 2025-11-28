"""
Service for Performance Analytics business logic.
"""
from typing import List, Dict, Any
from django.db.models import Count
from apps.analytics.models import Blog, BlogView
from apps.analytics.utils.filters import build_q_from_filter
from apps.analytics.utils.helpers import parse_timerange, safe_int, TRUNC_MAP


class PerformanceAnalyticsService:
    """Service class for performance analytics business logic."""

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
    def get_performance_analytics(
        compare: str,
        filters: Dict[str, Any] | None = None,
        user_id: int | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance analytics over time periods with growth metrics.
        
        Args:
            compare: Period size ('month', 'week', 'day', 'year')
            filters: Dynamic filter tree
            user_id: Optional user ID to filter by
            start: Start date in ISO format
            end: End date in ISO format
        
        Returns:
            List of dictionaries with x (period label), y (views), z (growth %)
        """
        if compare not in TRUNC_MAP:
            raise ValueError(f"Invalid compare value: {compare}. Must be one of {list(TRUNC_MAP.keys())}")

        trunc_func = TRUNC_MAP[compare]

        # Base querysets
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")
        blog_qs = Blog.objects.select_related("author", "country")

        # Apply filters to both querysets
        # Note: Filters should use field paths that work for BlogView (e.g., "blog.country.code")
        # For Blog queryset, we need to adjust the filter to remove "blog." prefix
        if filters:
            q = build_q_from_filter(filters)
            view_qs = view_qs.filter(q)
            # For Blog model, adjust filter field paths by removing "blog." prefix if present
            # This is a limitation: filters must be designed for BlogView model
            try:
                blog_qs = blog_qs.filter(q)
            except Exception:
                # If filter doesn't work for Blog model, skip filtering Blog queryset
                # This happens when filters reference "blog." prefix fields
                pass

        # Time range filters
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")
        blog_qs = parse_timerange(blog_qs, start, end, datetime_field="created_at")

        # User filter if provided
        if user_id:
            view_qs = view_qs.filter(blog__author__id=user_id)
            blog_qs = blog_qs.filter(author__id=user_id)

        # Aggregate views by period
        view_agg = (
            view_qs
            .annotate(period=trunc_func("viewed_at"))
            .values("period")
            .annotate(views_in_period=Count("id"))
            .order_by("period")
        )

        # Count blogs created per period
        blog_agg = (
            blog_qs
            .annotate(period=trunc_func("created_at"))
            .values("period")
            .annotate(blogs_in_period=Count("id"))
            .order_by("period")
        )

        # Convert to dict for quick lookup
        views_map = {row["period"]: row["views_in_period"] for row in view_agg}
        blogs_map = {row["period"]: row["blogs_in_period"] for row in blog_agg}

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

            # Format period label
            label = f"{period.isoformat()} ({blogs_count} blogs)"
            result.append({
                "x": label,
                "y": views,
                "z": (round(growth, 2) if growth is not None else None)
            })

        return result

