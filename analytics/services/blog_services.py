"""
Service for Blog Views Analytics business logic.
"""

from __future__ import annotations
from typing import List, Dict, Any, Callable, Optional
from django.db.models import Count, F, QuerySet
from analytics.models import BlogView
from analytics.utils.filters import build_q_from_filter
from analytics.utils.helpers import parse_timerange, detect_granularity, TRUNC_MAP
from config.logger import logger


def format_period(dt, granularity: str) -> str:
    """Format datetime object based on granularity."""
    if granularity == "day":
        return dt.strftime("%Y-%m-%d")
    if granularity == "week":
        return dt.strftime("%G-W%V")
    if granularity == "month":
        return dt.strftime("%Y-%m")
    return dt.strftime("%Y")  # year


class BlogViewsAnalyticsService:
    """Service class for blog views analytics business logic."""

    # Base queryset
    @staticmethod
    def _base_queryset() -> QuerySet:
        return BlogView.objects.select_related(
            "blog", "blog__author", "blog__author__user", "blog__country"
        )

    # Apply filters + time range
    @staticmethod
    def _apply_filters(
        qs: QuerySet,
        filters: Optional[Dict[str, Any]],
        start: Optional[str],
        end: Optional[str],
    ) -> QuerySet:
        if filters:
            qs = qs.filter(build_q_from_filter(filters))
            logger.debug(f"Filters applied. Remaining rows: {qs.count()}")
        qs = parse_timerange(qs, start, end, datetime_field="viewed_at")
        return qs

    # Generic aggregator for any type (user, country, etc.)
    @staticmethod
    def _aggregate(
        qs: QuerySet,
        group_fields: Dict[str, F],
        label_builder: Callable[[Dict[str, Any]], str],
        granularity: str,
    ) -> List[Dict[str, Any]]:
        trunc_func = TRUNC_MAP[granularity]
        annotated = qs.annotate(time_period=trunc_func("viewed_at"), **group_fields)
        grouped = (
            annotated.values(*group_fields.keys(), "time_period")
            .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
            .order_by("time_period", "-total_views")
        )
        return [
            {
                "x": f"{label_builder(row)} - {format_period(row['time_period'], granularity)}",
                "y": row["number_of_blogs"],
                "z": row["total_views"],
            }
            for row in grouped
        ]

    # Generic analytics handler
    @staticmethod
    def _get_analytics_generic(
        object_type: str,
        filters: Optional[Dict[str, Any]],
        start: Optional[str],
        end: Optional[str],
    ) -> List[Dict[str, Any]]:
        logger.debug(f"Generic analytics for type={object_type}")
        qs = BlogViewsAnalyticsService._base_queryset()
        qs = BlogViewsAnalyticsService._apply_filters(qs, filters, start, end)
        granularity = detect_granularity(start, end)

        CONFIG = {
            "country": {
                "group_fields": {"country_code": F("blog__country__code"), "country_name": F("blog__country__name")},
                "label": lambda row: row.get("country_name") or row.get("country_code") or "Unknown",
            },
            "user": {
                "group_fields": {"author_username": F("blog__author__user__username"), "author_id": F("blog__author__user__id")},
                "label": lambda row: f"{row.get('author_username') or 'unknown'} ({row.get('author_id')})",
            },
        }

        if object_type not in CONFIG:
            raise ValueError(f"Invalid analytics type: {object_type}")

        cfg = CONFIG[object_type]
        return BlogViewsAnalyticsService._aggregate(qs, cfg["group_fields"], cfg["label"], granularity)

    # Public API
    @staticmethod
    def  get_analytics(
        object_type: str,
        filters: Optional[Dict[str, Any]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for analytics.
        object_type: "user" | "country"
        """
        return BlogViewsAnalyticsService._get_analytics_generic(object_type, filters, start, end)

   