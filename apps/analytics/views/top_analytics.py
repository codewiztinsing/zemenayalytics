"""
Top Analytics View

Endpoint: /analytics/top/
- top: 'user'|'country'|'blog'
- time range fields: start, end (ISO)
- filters: dynamic filter tree
Returns top 10 by total views. x,y,z vary per 'top' selection.
"""
from django.db.models import Count, F
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.analytics.models import BlogView
from apps.analytics.utils.filters import build_q_from_filter
from apps.analytics.views.helpers import parse_timerange
from apps.analytics.serializers.top_analytics import (
    TopAnalyticsRequestSerializer,
    TopAnalyticsResponseSerializer,
)
from apps.analytics.pagination import ConfigurablePageNumberPagination


class TopAnalyticsView(APIView):
    """Analytics view for top 10 users, countries, or blogs by views."""
    
    pagination_class = ConfigurablePageNumberPagination

    @extend_schema(
        operation_id="top_analytics",
        summary="Get top analytics",
        description="""
        Get top 10 users, countries, or blogs by total views.
        Returns the top performers based on view counts.
        """,
        tags=["Analytics"],
        request=TopAnalyticsRequestSerializer,
        responses={
            200: TopAnalyticsResponseSerializer(many=True),
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        }
    )
    def post(self, request: Request) -> Response:  # type: ignore[override]
        serializer = TopAnalyticsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        top = validated_data.get("top", "blog")
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        if filters:
            view_qs = view_qs.filter(build_q_from_filter(filters))
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        # Annotate totals per requested top
        if top == "user":
            qs = (
                view_qs
                .values(user_id=F("blog__author__id"), user_name=F("blog__author__username"))
                .annotate(total_views=Count("id"), blogs_count=Count("blog", distinct=True))
                .order_by("-total_views")[:10]
            )
            result = [
                {"x": r["user_name"], "y": r["blogs_count"], "z": r["total_views"]}
                for r in qs
            ]
            
            # Paginate results
            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(result, request)
            response_serializer = TopAnalyticsResponseSerializer(paginated_result, many=True)
            return paginator.get_paginated_response(response_serializer.data)

        if top == "country":
            qs = (
                view_qs
                .values(country_code=F("blog__country__code"), country_name=F("blog__country__name"))
                .annotate(total_views=Count("id"), blogs_count=Count("blog", distinct=True))
                .order_by("-total_views")[:10]
            )
            result = [
                {"x": r["country_name"] or r["country_code"], "y": r["blogs_count"], "z": r["total_views"]}
                for r in qs
            ]
            
            # Paginate results
            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(result, request)
            response_serializer = TopAnalyticsResponseSerializer(paginated_result, many=True)
            return paginator.get_paginated_response(response_serializer.data)

        # default: blog
        qs = (
            view_qs
            .values(blog_id=F("blog__id"), blog_title=F("blog__title"))
            .annotate(total_views=Count("id"))
            .order_by("-total_views")[:10]
        )
        result = [
            {"x": r["blog_title"], "y": r["blog_id"], "z": r["total_views"]} for r in qs
        ]
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = TopAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)

