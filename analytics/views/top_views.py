"""
Top Analytics View

Endpoint: /analytics/top/
- top: 'user'|'country'|'blog'
- time range fields: start, end (ISO)
- filters: dynamic filter tree
Returns top 10 by total views. x,y,z vary per 'top' selection.
"""
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import OpenApiParameter

from analytics.serializers.top_serializers import (
    TopAnalyticsRequestSerializer,
    TopAnalyticsResponseSerializer,
)
from analytics.pagination import ConfigurablePageNumberPagination
from analytics.services.top_service import TopAnalyticsService
from analytics.utils.helpers import parse_query_params
from analytics.utils.swagger import SwaggerMixin, create_enum_parameter, create_integer_parameter
from config.logger import logger


class TopAnalyticsView(SwaggerMixin, APIView):
    """Analytics view for top 10 users, countries, or blogs by views."""
    
    pagination_class = ConfigurablePageNumberPagination
    
    # Swagger configuration
    swagger_operation_id = "top_analytics"
    swagger_summary = "Get top analytics"
    swagger_description = """
    Get top 10 users, countries, or blogs by total views.
    Returns the top performers based on view counts.
    """
    swagger_request_serializer = TopAnalyticsRequestSerializer
    swagger_response_serializer = TopAnalyticsResponseSerializer
    
    def get_swagger_parameters(self):
        """Get Swagger parameters including view-specific ones."""
        return self.get_common_parameters() + [
            create_enum_parameter(
                name="top",
                description="The type of top analytics to retrieve",
                enum_values=["user", "country", "blog"],
                required=False,
            ),
            create_integer_parameter(
                name="limit",
                description="The number of top results to return",
                required=False,
            ),
        ]
    
    def get(self, request: Request) -> Response:  # type: ignore[override]
        """
        Handle GET requests using query parameters to retrieve top analytics.
        """
        logger.info(f"Top analytics request received from {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        # Parse query parameters using helper function
        data = parse_query_params(request.query_params)
        
        serializer = TopAnalyticsRequestSerializer(data=data)
        if not serializer.is_valid():
            logger.warning(f"Invalid request data: {serializer.errors}")
            serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        top = validated_data.get("top", "blog")
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        logger.info(f"Fetching top analytics - top: {top}, start: {start}, end: {end}")

        # Use service to get top analytics data
        try:
            result = TopAnalyticsService.get_top_analytics(
                top=top,
                filters=filters,
                start=start,
                end=end,
                limit=10,
            )
            logger.info(f"Successfully retrieved {len(result)} top analytics records")
        except ValueError as e:
            logger.error(f"Invalid filter format: {str(e)}")
            return Response(
                {"detail": f"Invalid filter format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in top analytics: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = TopAnalyticsResponseSerializer(paginated_result, many=True)
        logger.debug(f"Returning paginated response with {len(paginated_result)} items")
        return paginator.get_paginated_response(response_serializer.data)


# Apply Swagger schema decorator to the get method
TopAnalyticsView.get = TopAnalyticsView().get_swagger_schema_decorator()(TopAnalyticsView.get)

