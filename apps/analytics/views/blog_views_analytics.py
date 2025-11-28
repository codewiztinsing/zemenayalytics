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
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.analytics.serializers.blog_views_analytics import (
    BlogViewsAnalyticsRequestSerializer,
    BlogViewsAnalyticsResponseSerializer,
)
from apps.analytics.pagination import ConfigurablePageNumberPagination
from apps.analytics.services.blog_views_analytics_service import BlogViewsAnalyticsService


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
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        # Use service to get analytics data
        result = BlogViewsAnalyticsService.get_analytics(
            object_type=object_type,
            filters=filters,
            start=start,
            end=end,
        )
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = BlogViewsAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)

