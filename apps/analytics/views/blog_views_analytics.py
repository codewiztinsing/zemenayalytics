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
import json
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter

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
        parameters=[
            OpenApiParameter(
                name="object_type",
                description="The type of object to group by",
                required=False,
                type=str,
                enum=["country", "user"]
            ),
            OpenApiParameter(
                name="filters",
                description="The filters to apply to the analytics",
                required=False,
                type=dict
            ),
            OpenApiParameter(
                name="start",
                description="The start date of the analytics (ISO format: YYYY-MM-DD)",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="end",
                description="The end date of the analytics (ISO format: YYYY-MM-DD)",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="range",
                description="The range of the analytics",
                required=False,
                type=str,
                enum=["month", "week", "year", "day"]
            ),
            OpenApiParameter(
                name="page",
                description="The page number of the analytics",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="page_size",
                description="The page size of the analytics",
                required=False,
                type=int
            ),
        ],
        responses={
            200: BlogViewsAnalyticsResponseSerializer(many=True),
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        }
    )

    def get(self, request: Request) -> Response:  # type: ignore[override]
        """
        Handle GET requests using query parameters to retrieve blog views analytics.
        """
        # DRF exposes query parameters via request.query_params (a QueryDict)
        # Convert QueryDict to a regular dict and parse JSON fields
        data = {}
        for key, value in request.query_params.items():
            # QueryDict returns lists, get the first element
            if isinstance(value, list):
                value = value[0] if value else None
            # Convert empty strings to None for optional fields
            if value == "":
                value = None
            data[key] = value
        
        # Parse filters from JSON string if provided
        if "filters" in data and data["filters"]:
            try:
                # Parse JSON string to dict
                data["filters"] = json.loads(data["filters"])
            except (json.JSONDecodeError, TypeError):
                # If it's not valid JSON, pass it as-is and let serializer handle validation
                pass
        
        serializer = BlogViewsAnalyticsRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        object_type = validated_data.get("object_type", "country")
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        # Use service to get analytics data
        try:
            result = BlogViewsAnalyticsService.get_analytics(
                object_type=object_type,
                filters=filters,
                start=start,
                end=end,
            )
        except ValueError as e:
            return Response(
                {"detail": f"Invalid filter format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = BlogViewsAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)


