"""
Blog Views Analytics View

Endpoint: /analytics/blog-views/
- object_type: 'country' | 'user'
- start/end: Date range (ISO format: YYYY-MM-DD)
- filters: JSON filter object (dynamic filters)
- Time granularity is automatically determined from date range:
  * 1-7 days: day
  * 8-30 days: week
  * 31-365 days: month
  * >365 days: year
Response:
  [
    { "x": "<grouping key> - <time period>", "y": number_of_blogs, "z": total_views },
    ...
  ]
Aggregation:
  Group blogs (distinct blog count) and total views per grouping key AND time period.
"""
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import OpenApiParameter

from analytics.serializers.blog_serializers import (
    BlogViewsAnalyticsRequestSerializer,
    BlogViewsAnalyticsResponseSerializer,
)
from analytics.pagination import ConfigurablePageNumberPagination
from analytics.services.blog_services import BlogViewsAnalyticsService
from analytics.utils.helpers import parse_query_params
from analytics.utils.swagger import SwaggerMixin, create_enum_parameter
from config.logger import logger


class BlogViewsAnalyticsView(SwaggerMixin, APIView):
    """Analytics view for blog views grouped by country or user."""
    
    pagination_class = ConfigurablePageNumberPagination
    
    # Swagger configuration
    swagger_operation_id = "blog_views_analytics"
    swagger_summary = "Get blog views analytics"
    swagger_description = """
    Get analytics for blog views grouped by country or user and time period.
    Time granularity (day/week/month/year) is automatically determined from the date range.
    Returns aggregated data with number of blogs and total views per grouping key and time period.
    """
    swagger_request_serializer = BlogViewsAnalyticsRequestSerializer
    swagger_response_serializer = BlogViewsAnalyticsResponseSerializer
    
    def get_swagger_parameters(self):
        """Get Swagger parameters including view-specific ones."""
        return self.get_common_parameters() + [
            create_enum_parameter(
                name="object_type",
                description="The type of object to group by",
                enum_values=["country", "user"],
                required=False,
            ),
        ]
    
    def get(self, request: Request) -> Response:
        """
        Handle GET requests using query parameters to retrieve blog views analytics.
        """
        logger.info(f"Blog views analytics request received from {request.META.get('REMOTE_ADDR', 'unknown')}")

        # Build a cache key based on full request path + query string
        cache_key = f"blog_views_analytics:{request.get_full_path()}"
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            logger.debug("Returning cached response for BlogViewsAnalyticsView")
            return Response(cached_payload, status=status.HTTP_200_OK)

        # Parse query parameters using helper function
        data = parse_query_params(request.query_params)

        serializer = BlogViewsAnalyticsRequestSerializer(data=data)
        if not serializer.is_valid():
            logger.warning(f"Invalid request data: {serializer.errors}")
            serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        object_type = validated_data.get("object_type", "country")
        filters = validated_data.get("filters")
        start = validated_data.get("start")
        end = validated_data.get("end")

        logger.info(f"Fetching blog views analytics - object_type: {object_type}, start: {start}, end: {end}")

        # Use service to get analytics data
        try:
            result = BlogViewsAnalyticsService.get_analytics(
                object_type=object_type,
                filters=filters,
                start=start,
                end=end,
            )
            cache.set(cache_key, result, timeout=300)
            logger.info(f"Successfully retrieved {len(result)} analytics records")
        except ValueError as e:
            logger.error(f"Invalid filter format: {str(e)}")
            return Response(
                {"detail": f"Invalid filter format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Unexpected error in blog views analytics: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = BlogViewsAnalyticsResponseSerializer(paginated_result, many=True)
        response = paginator.get_paginated_response(response_serializer.data)

        # Cache the final paginated payload
        cache_timeout = getattr(settings, "BLOG_VIEWS_ANALYTICS_CACHE_TIMEOUT", 300)
        cache.set(cache_key, response.data, timeout=cache_timeout)

        logger.debug(f"Returning paginated response with {len(paginated_result)} items (cached for {cache_timeout}s)")
        return response


# Apply Swagger schema decorator to the get method
BlogViewsAnalyticsView.get = BlogViewsAnalyticsView().get_swagger_schema_decorator()(BlogViewsAnalyticsView.get)

