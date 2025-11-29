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
import json
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.analytics.serializers.performance_analytics import (
    PerformanceAnalyticsRequestSerializer,
    PerformanceAnalyticsResponseSerializer,
)
from apps.analytics.pagination import ConfigurablePageNumberPagination
from apps.analytics.services.performance_analytics_service import PerformanceAnalyticsService


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
        parameters=[
            OpenApiParameter(
                name="compare",
                description="The period size for comparison",
                required=False,
                type=str,
                enum=["month", "week", "day", "year"]
            ),
            OpenApiParameter(
                name="user_id",
                description="Optional user ID to filter performance for a single user",
                required=False,
                type=int
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
            200: PerformanceAnalyticsResponseSerializer(many=True),
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        }
    )

    def get(self, request: Request) -> Response:  # type: ignore[override]
        """
        Handle GET requests using query parameters to retrieve performance analytics.
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
        
        serializer = PerformanceAnalyticsRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        compare = validated_data.get("compare", "month")
        filters = validated_data.get("filters")
        user_id = validated_data.get("user_id")
        start = validated_data.get("start")
        end = validated_data.get("end")

        try:
            # Use service to get performance analytics data
            result = PerformanceAnalyticsService.get_performance_analytics(
                compare=compare,
                filters=filters,
                user_id=user_id,
                start=start,
                end=end,
            )
        except ValueError as e:
            error_message = str(e)
            # Check if it's a filter validation error
            if "filter" in error_message.lower() or "Unsupported filter" in error_message:
                return Response(
                    {"detail": f"Invalid filter format: {error_message}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = PerformanceAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)
