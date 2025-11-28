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
from drf_spectacular.utils import extend_schema

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

