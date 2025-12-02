"""
Service for Top Analytics business logic.
"""

from typing import List, Dict, Any, Callable
from django.db.models import Count, F, QuerySet
from analytics.models import BlogView
from analytics.utils.filters import build_q_from_filter
from analytics.utils.helpers import parse_timerange
from config.logger import logger


class TopAnalyticsService:
    """Service class for top analytics business logic."""

    # -------------------------------------------------------------------------
    # WRAPPER: Build Base QuerySet (filters + datetime + select_related)
    # -------------------------------------------------------------------------
    @staticmethod
    def _base_queryset(
        filters: Dict[str, Any] | None,
        start: str | None,
        end: str | None,
    ) -> QuerySet:
        qs = BlogView.objects.select_related(
            "blog",
            "blog__author",
            "blog__country",
            "blog__author__user",
        )

        if filters:
            qs = qs.filter(build_q_from_filter(filters))

        qs = parse_timerange(qs, start, end, datetime_field="viewed_at")
        return qs

    # -------------------------------------------------------------------------
    # WRAPPER: Config resolver for country/blog/user
    # -------------------------------------------------------------------------
    @staticmethod
    def _get_config(top_type: str) -> Dict[str, Any]:
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

        return config[top_type]

    # -------------------------------------------------------------------------
    # WRAPPER: Execute aggregation queryset
    # -------------------------------------------------------------------------
    @staticmethod
    def _aggregate(
        qs: QuerySet,
        values: Dict[str, Any],
        annotate: Dict[str, Any],
        limit: int,
    ) -> QuerySet:
        return (
            qs.values(**values)
            .annotate(**annotate)
            .order_by("-z")[:limit]
        )

    # -------------------------------------------------------------------------
    # WRAPPER: Serialize one row
    # -------------------------------------------------------------------------
    @staticmethod
    def _serialize_row(row: Dict[str, Any], resolve_x: Callable) -> Dict[str, Any]:
        return {
            "x": resolve_x(row),
            "y": row.get("y"),
            "z": row["z"],
        }

    # -------------------------------------------------------------------------
    # UNIFIED HANDLER
    # -------------------------------------------------------------------------
    @staticmethod
    def get_top_generic(
        top_type: str,
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        qs = TopAnalyticsService._base_queryset(filters, start, end)
        cfg = TopAnalyticsService._get_config(top_type)
        

        logger.info(f"Base queryset: {qs.query}")
        logger.info(f"Config: {cfg}")


        agg_qs = TopAnalyticsService._aggregate(
            qs,
            values=cfg["values"],
            annotate=cfg["annotate"],
            limit=limit,
        )

        return [
            TopAnalyticsService._serialize_row(row, cfg["resolve_x"])
            for row in agg_qs
        ]


    @staticmethod
    def get_top_analytics(
        top: str,
        filters: Dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if top in ("country", "blog", "user"):
            return TopAnalyticsService.get_top_generic(
                top_type=top,
                filters=filters,
                start=start,
                end=end,
                limit=limit,
            )

        raise ValueError(f"Invalid top analytics type: {top}")
