"""
Service for Top Analytics business logic.
"""
from typing import List, Dict, Any
from django.db.models import Count, F
from apps.analytics.models import BlogView
from apps.analytics.utils.filters import build_q_from_filter
from apps.analytics.utils.helpers import parse_timerange


class TopAnalyticsService:
    """Service class for top analytics business logic."""

    @staticmethod
    def get_top_users(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top users by total views.
        
        Args:
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
            limit: Number of top results to return
        
        Returns:
            List of dictionaries with x (user name), y (blogs count), z (total views)
        """
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        if filters:
            view_qs = view_qs.filter(build_q_from_filter(filters))
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        qs = (
            view_qs
            .values(author_id=F("blog__author__id"), author_username=F("blog__author__username"))
            .annotate(total_views=Count("id"), blogs_count=Count("blog_id", distinct=True))
            .order_by("-total_views")[:limit]
        )

        result = [
            {"x": r["author_username"], "y": r["blogs_count"], "z": r["total_views"]}
            for r in qs
        ]

        return result

    @staticmethod
    def get_top_countries(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top countries by total views.
        
        Args:
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
            limit: Number of top results to return
        
        Returns:
            List of dictionaries with x (country name), y (blogs count), z (total views)
        """
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        if filters:
            view_qs = view_qs.filter(build_q_from_filter(filters))
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        qs = (
            view_qs
            .values(country_code=F("blog__country__code"), country_name=F("blog__country__name"))
            .annotate(total_views=Count("id"), blogs_count=Count("blog_id", distinct=True))
            .order_by("-total_views")[:limit]
        )

        result = [
            {"x": r["country_name"] or r["country_code"], "y": r["blogs_count"], "z": r["total_views"]}
            for r in qs
        ]

        return result

    @staticmethod
    def get_top_blogs(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top blogs by total views.
        
        Args:
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
            limit: Number of top results to return
        
        Returns:
            List of dictionaries with x (blog title), y (blog id), z (total views)
        """
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        if filters:
            view_qs = view_qs.filter(build_q_from_filter(filters))
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        qs = (
            view_qs
            .values(blog_id_val=F("blog__id"), blog_title=F("blog__title"))
            .annotate(total_views=Count("id"))
            .order_by("-total_views")[:limit]
        )

        result = [
            {"x": r["blog_title"], "y": r["blog_id_val"], "z": r["total_views"]} for r in qs
        ]

        return result

    @staticmethod
    def get_top_analytics(
        top: str,
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top analytics by type.
        
        Args:
            top: 'user', 'country', or 'blog'
            filters: Dynamic filter tree
            start: Start date in ISO format
            end: End date in ISO format
            limit: Number of top results to return
        
        Returns:
            List of dictionaries with top analytics data
        """
        if top == "user":
            return TopAnalyticsService.get_top_users(filters, start, end, limit)
        elif top == "country":
            return TopAnalyticsService.get_top_countries(filters, start, end, limit)
        else:
            return TopAnalyticsService.get_top_blogs(filters, start, end, limit)

