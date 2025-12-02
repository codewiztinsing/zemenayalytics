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
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import OpenApiParameter

from analytics.serializers.performance_serializers import (
    PerformanceAnalyticsRequestSerializer,
    PerformanceAnalyticsResponseSerializer,
)
from analytics.pagination import ConfigurablePageNumberPagination
from analytics.services.performance_service import PerformanceAnalyticsService
from analytics.utils.helpers import parse_query_params
from analytics.utils.swagger import SwaggerMixin, create_enum_parameter, create_integer_parameter
from config.logger import logger


class PerformanceAnalyticsView(SwaggerMixin, APIView):
    """Analytics view for performance metrics over time periods."""
    
    pagination_class = ConfigurablePageNumberPagination
    
    # Swagger configuration
    swagger_operation_id = "performance_analytics"
    swagger_summary = "Get performance analytics"
    swagger_description = """
    Get performance analytics over time periods with growth metrics.
    Returns views per period along with growth percentage compared to previous period.
    """
    swagger_request_serializer = PerformanceAnalyticsRequestSerializer
    swagger_response_serializer = PerformanceAnalyticsResponseSerializer
    
    def get_swagger_parameters(self):
        """Get Swagger parameters including view-specific ones."""
        return self.get_common_parameters() + [
            create_enum_parameter(
                name="compare",
                description="The period size for comparison",
                enum_values=["month", "week", "day", "year"],
                required=False,
                default="month",
            ),
            create_integer_parameter(
                name="user_id",
                description="Optional user ID to filter performance for a single user",
                required=False,
            ),
        ]
    
    def get(self, request: Request) -> Response:  # type: ignore[override]
        """
        Handle GET requests using query parameters to retrieve performance analytics.
        """
        logger.info(f"Performance analytics request received from {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        # Parse query parameters using helper function
        data = parse_query_params(request.query_params)
        
        serializer = PerformanceAnalyticsRequestSerializer(data=data)
        if not serializer.is_valid():
            logger.warning(f"Invalid request data: {serializer.errors}")
            serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        compare = validated_data.get("compare", "month")
        filters = validated_data.get("filters")
        user_id = validated_data.get("user_id")
        start = validated_data.get("start")
        end = validated_data.get("end")

        logger.info(f"Fetching performance analytics - compare: {compare}, user_id: {user_id}, start: {start}, end: {end}")

        try:
            # Use service to get performance analytics data
            result = PerformanceAnalyticsService.get_performance_analytics(
                compare=compare,
                filters=filters,
                user_id=user_id,
                start=start,
                end=end,
            )
            logger.info(f"Successfully retrieved {len(result)} performance analytics records")
        except ValueError as e:
            error_message = str(e)
            logger.error(f"Invalid parameter in performance analytics: {error_message}")
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
        except Exception as e:
            logger.error(f"Unexpected error in performance analytics: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = PerformanceAnalyticsResponseSerializer(paginated_result, many=True)
        logger.debug(f"Returning paginated response with {len(paginated_result)} items")
        return paginator.get_paginated_response(response_serializer.data)


# Apply Swagger schema decorator to the get method
PerformanceAnalyticsView.get = PerformanceAnalyticsView().get_swagger_schema_decorator()(PerformanceAnalyticsView.get)
