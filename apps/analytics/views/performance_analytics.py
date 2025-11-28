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
from drf_spectacular.utils import extend_schema

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
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Paginate results
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        response_serializer = PerformanceAnalyticsResponseSerializer(paginated_result, many=True)
        return paginator.get_paginated_response(response_serializer.data)

