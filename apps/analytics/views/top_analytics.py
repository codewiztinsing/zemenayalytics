"""
Top Analytics View

Endpoint: /analytics/top/
- top: 'user'|'country'|'blog'
- time range fields: start, end (ISO)
- filters: dynamic filter tree
Returns top 10 by total views. x,y,z vary per 'top' selection.
"""
import json
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.analytics.serializers.top_analytics import (
    TopAnalyticsRequestSerializer,
    TopAnalyticsResponseSerializer,
)
from apps.analytics.pagination import ConfigurablePageNumberPagination
from apps.analytics.services.top_analytics_service import TopAnalyticsService


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
        parameters=[
            OpenApiParameter(
                name="top",
                description="The type of top analytics to retrieve",
                required=False,
                type=str,
                enum=["user", "country", "blog"]
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
                name="limit",
                description="The number of top results to return",
                required=False,
                type=int
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
            200: TopAnalyticsResponseSerializer(many=True),
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        }
    )

    def get(self, request: Request) -> Response:  # type: ignore[override]
        """
        Handle GET requests using query parameters to retrieve top analytics.
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
        
        serializer = TopAnalyticsRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        top = validated_data.get("top", "blog")
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        # Use service to get top analytics data
        try:
            result = TopAnalyticsService.get_top_analytics(
                top=top,
                filters=filters,
                start=start,
                end=end,
                limit=10,
            )
        except ValueError as e:
            return Response(
                {"detail": f"Invalid filter format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = TopAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)

