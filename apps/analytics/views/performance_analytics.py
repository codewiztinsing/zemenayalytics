"""
Performance Analytics View

Endpoint: /analytics/performance/
- compare: 'month'|'week'|'day'|'year' (period size)
- user_id optional (if provided, performance for single user; otherwise all users)
- filters: dynamic filters applied before aggregation
Response per period:
  { "x": "<period label> (n_blogs)", "y": views_in_period, "z": growth_pct_vs_previous_period }
Implementation notes:
  - We count blog creations in the period (number_of_blogs).
  - We sum views within the same period.
  - Growth is computed relative to previous period's views; when previous = 0 use None or 100%.
"""
from typing import Any, Dict, List
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.analytics.models import Blog, BlogView
from apps.analytics.utils.filters import build_q_from_filter
from apps.analytics.views.helpers import parse_timerange, safe_int, TRUNC_MAP
from apps.analytics.serializers.performance_analytics import (
    PerformanceAnalyticsRequestSerializer,
    PerformanceAnalyticsResponseSerializer,
)
from apps.analytics.pagination import ConfigurablePageNumberPagination


class PerformanceAnalyticsView(APIView):
    """Analytics view for performance metrics over time periods."""
    
    pagination_class = ConfigurablePageNumberPagination

    @extend_schema(
        operation_id="performance_analytics",
        summary="Get performance analytics",
        description="""
        Get performance analytics over time periods with growth metrics.
        Returns views per period along with growth percentage compared to previous period.
        """,
        tags=["Analytics"],
        request=PerformanceAnalyticsRequestSerializer,
        responses={
            200: PerformanceAnalyticsResponseSerializer(many=True),
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        }
    )
    def post(self, request: Request) -> Response:  # type: ignore[override]
        serializer = PerformanceAnalyticsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        compare = validated_data.get("compare", "month")
        filters = validated_data.get("filters")
        user_id = validated_data.get("user_id")
        start = validated_data.get("start")
        end = validated_data.get("end")

        trunc_func = TRUNC_MAP[compare]

        # Base view queryset for counting views
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")
        blog_qs = Blog.objects.select_related("author", "country")

        # Apply filters to both view and blog querysets.
        # Filters may refer to blog fields (created_at) or view fields (viewed_at).
        if filters:
            q = build_q_from_filter(filters)
            # Apply to both querysets; some lookups won't match but that's ok.
            view_qs = view_qs.filter(q)
            blog_qs = blog_qs.filter(q)

        # Time range filters if present
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")
        blog_qs = parse_timerange(blog_qs, start, end, datetime_field="created_at")

        if user_id:
            view_qs = view_qs.filter(blog__author__id=user_id)
            blog_qs = blog_qs.filter(author__id=user_id)

        # Aggregate views by period
        # First annotate each view's period
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

        # Convert to dict for quick lookup; avoid N+1 and extra DB hits
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
            if prev_views is None:
                growth = None
            else:
                if prev_views == 0:
                    growth = None if views == 0 else 100.0
                else:
                    growth = (views - prev_views) / prev_views * 100.0
            prev_views = views
            # label period -> str(period) is localized UTC timestamp; convert to isoformat for clarity
            label = f"{period.isoformat()} ({blogs_count} blogs)"
            result.append({"x": label, "y": views, "z": (round(growth, 2) if growth is not None else None)})

        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = PerformanceAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)

