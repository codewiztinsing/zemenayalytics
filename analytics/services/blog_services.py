"""
Service for Blog Views Analytics business logic.
"""
from typing import List, Dict, Any
from django.db.models import Count, F, QuerySet
from analytics.models import BlogView
from analytics.utils.filters import build_q_from_filter
from analytics.utils.helpers import parse_timerange
from config.logger import logger


class BlogViewsAnalyticsService:
    """Service class for blog views analytics business logic."""

    @staticmethod
    def get_analytics_by_country(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get blog views analytics grouped by country.
        
        Args:
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
        
        Returns:
            List of dictionaries with x (country name), y (number of blogs), z (total views)
        """
        logger.debug(f"Getting analytics by country - filters: {filters}, start: {start}, end: {end}")
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        # Apply dynamic filters if provided
        if filters:
            q = build_q_from_filter(filters)
            view_qs = view_qs.filter(q)
            logger.debug(f"Applied filters, queryset count: {view_qs.count()}")

        # Apply time range to the view timestamp
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        # Aggregate by country
        agg_qs = (
            view_qs
            .values(country_code=F("blog__country__code"), country_name=F("blog__country__name"))
            .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
            .order_by("-total_views")
        )

        # Map to expected x,y,z format
        result = [
            {"x": f"{r['country_name'] or r['country_code']}", "y": r["number_of_blogs"], "z": r["total_views"]}
            for r in agg_qs
        ]

        logger.info(f"Retrieved {len(result)} country analytics records")
        return result

    @staticmethod
    def get_analytics_by_user(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get blog views analytics grouped by user.
        
        Args:
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
        
        Returns:
            List of dictionaries with x (user), y (number of blogs), z (total views)
        """
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        # Apply dynamic filters if provided
        if filters:
            q = build_q_from_filter(filters)
            view_qs = view_qs.filter(q)

        # Apply time range to the view timestamp
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        # Aggregate by user
        agg_qs = (
            view_qs
            .values(author_username=F("blog__author__user__username"), author_id=F("blog__author__user__id"))
            .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
            .order_by("-total_views")
        )

        # Map to expected x,y,z format
        result = [
            {"x": f"{r['author_username']} ({r['author_id']})", "y": r["number_of_blogs"], "z": r["total_views"]}
            for r in agg_qs
        ]

        logger.info(f"Retrieved {len(result)} user analytics records")
        return result

    @staticmethod
    def get_analytics(
        object_type: str,
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get blog views analytics grouped by object_type.
        
        Args:
            object_type: 'country' or 'user'
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
        
        Returns:
            List of dictionaries with analytics data
        """
        logger.debug(f"Getting analytics for object_type: {object_type}")
        if object_type == "user":
            return BlogViewsAnalyticsService.get_analytics_by_user(filters, start, end)
        else:
            return BlogViewsAnalyticsService.get_analytics_by_country(filters, start, end)

