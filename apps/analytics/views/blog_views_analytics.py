"""
Blog Views Analytics View

Endpoint: /analytics/blog-views/
- object_type: 'country' | 'user'
- range: 'month'|'week'|'year'|'day'
- filters: JSON filter object (dynamic filters)
Response:
  [
    { "x": "<grouping key>", "y": number_of_blogs, "z": total_views },
    ...
  ]
Aggregation:
  group blogs (distinct blog count) and total views per grouping key.
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
from apps.analytics.serializers.blog_views_analytics import (
    BlogViewsAnalyticsRequestSerializer,
    BlogViewsAnalyticsResponseSerializer,
)
from apps.analytics.pagination import ConfigurablePageNumberPagination


class BlogViewsAnalyticsView(APIView):
    """Analytics view for blog views grouped by country or user."""
    
    pagination_class = ConfigurablePageNumberPagination

    @extend_schema(
        operation_id="blog_views_analytics",
        summary="Get blog views analytics",
        description="""
        Get analytics for blog views grouped by country or user.
        Returns aggregated data with number of blogs and total views per grouping key.
        """,
        tags=["Analytics"],
        request=BlogViewsAnalyticsRequestSerializer,
        responses={
            200: BlogViewsAnalyticsResponseSerializer(many=True),
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        }
    )
    def post(self, request: Request) -> Response:  # type: ignore[override]
        serializer = BlogViewsAnalyticsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        object_type = validated_data.get("object_type", "country")
        time_range = validated_data.get("range")
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        # Base queryset: join Blog and BlogView
        # We want: group by object_type value, count distinct blogs, sum views rows
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        # Apply dynamic filters if provided
        if filters:
            q = build_q_from_filter(filters)
            # filters may refer to fields from Blog, BlogView, User, Country; Q handles double-underscore
            view_qs = view_qs.filter(q)

        # Apply time range to the view timestamp
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        # Decide grouping key
        if object_type == "user":
            # group by blog author
            # annotate author username or id as x, number of distinct blogs y, z total views
            agg_qs = (
                view_qs
                .values(author_username=F("blog__author__username"), author_id=F("blog__author__id"))
                .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
                .order_by("-total_views")
            )
            # Map to expected x,y,z
            result = [
                {"x": f"{r['author_username']} ({r['author_id']})", "y": r["number_of_blogs"], "z": r["total_views"]}
                for r in agg_qs
            ]
            
            # Paginate results
            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(result, request)
            response_serializer = BlogViewsAnalyticsResponseSerializer(paginated_result, many=True)
            return paginator.get_paginated_response(response_serializer.data)

        # default: country
        agg_qs = (
            view_qs
            .values(country_code=F("blog__country__code"), country_name=F("blog__country__name"))
            .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
            .order_by("-total_views")
        )
        result = [
            {"x": f"{r['country_name'] or r['country_code']}", "y": r["number_of_blogs"], "z": r["total_views"]}
            for r in agg_qs
        ]
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = BlogViewsAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)

