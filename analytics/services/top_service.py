"""
Service for Top Analytics business logic.
"""

from typing import List, Dict, Any
from django.db.models import Count, F, QuerySet
from analytics.models import BlogView
from analytics.utils.filters import build_q_from_filter
from analytics.utils.helpers import parse_timerange


class TopAnalyticsService:
    """Service class for top analytics business logic."""

    # ---------------------------------------------------------
    # Internal Helper → prepares queryset for all top analytics
    # ---------------------------------------------------------
    @staticmethod
    def _prepare_queryset(
        filters: Dict[str, Any] | None,
        start: str | None,
        end: str | None,
    ) -> QuerySet:
        """
        Returns the base queryset with filters + date range applied.
        """
        qs = BlogView.objects.select_related(
            "blog",
            "blog__author",
            "blog__country",
            "blog__author__user",
        )

        if filters:
            qs = qs.filter(build_q_from_filter(filters))

        # filter on BlogView.viewed_at using parse_timerange.
        qs = parse_timerange(qs, start, end, datetime_field="viewed_at")
        return qs


    # ---------------------------------------------------------
    # Unified TOP COUNTRIES + TOP BLOGS + TOP USERS
    # ---------------------------------------------------------
    @staticmethod
    def get_top_generic(
        top_type: str,
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Unified handler for 'country' and 'blog' top analytics.

        Returns list of:
            x → label (country name / blog title)
            y → secondary metric (blogs_count OR blog_id)
            z → total views
        """

        qs = TopAnalyticsService._prepare_queryset(filters, start, end)

        # Configuration mapping
        config = {
            "country": {
                "values": {
                    "x_code": F("blog__country__code"),
                    "x_name": F("blog__country__name"),
                },
                "annotate": {
                    "z": Count("id"),
                    "y": Count("blog_id", distinct=True),
                },
                "resolve_x": lambda r: r["x_name"] or r["x_code"],
            },
            "blog": {
                "values": {
                    "x": F("blog__title"),
                    "y": F("blog__id"),
                },
                "annotate": {
                    "z": Count("id"),
                },
                "resolve_x": lambda r: r["x"],
            },
            "user": {
                "values": {
                    "x_username": F("blog__author__user__username"),
                    "y": F("blog__author__user__id"),
                },
                "annotate": {
                    "z": Count("id"),
                },
                "resolve_x": lambda r: r["x_username"],
            },
        }

        if top_type not in config:
            raise ValueError(f"Invalid top_type: {top_type}")

        cfg = config[top_type]

        qs = (
            qs.values(**cfg["values"])
            .annotate(**cfg["annotate"])
            .order_by("-z")[:limit]
        )

        results = []
        for r in qs:
            results.append(
                {
                    "x": cfg["resolve_x"](r),
                    "y": r.get("y"),
                    "z": r["z"],
                }
            )

        return results

    # ---------------------------------------------------------
    # Main Router
    # ---------------------------------------------------------
    @staticmethod
    def get_top_analytics(
        top: str,
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Entry point for top analytics.
        """
        if top == "user":
            return TopAnalyticsService.get_top_generic(top, filters, start, end, limit)

        if top in ("country", "blog"):
            return TopAnalyticsService.get_top_generic(top, filters, start, end, limit)

        raise ValueError(f"Invalid top analytics type: {top}")

    # ------------------------------------------------------------------
    # Backwards-compatible helpers used by existing unit tests
    # ------------------------------------------------------------------
    @staticmethod
    def get_top_blogs(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper kept for tests.
        Delegates to get_top_generic with top_type='blog'.
        """
        return TopAnalyticsService.get_top_generic(
            top_type="blog",
            filters=filters,
            start=start,
            end=end,
            limit=limit,
        )

    @staticmethod
    def get_top_countries(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper kept for tests.
        Delegates to get_top_generic with top_type='country'.
        """
        return TopAnalyticsService.get_top_generic(
            top_type="country",
            filters=filters,
            start=start,
            end=end,
            limit=limit,
        )

    @staticmethod
    def get_top_users(
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper kept for tests.
        Delegates to get_top_generic with top_type='user'.
        """
        return TopAnalyticsService.get_top_generic(
            top_type="user",
            filters=filters,
            start=start,
            end=end,
            limit=limit,
        )
