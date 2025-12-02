"""
Serializers for Performance Analytics endpoint.
"""
from rest_framework import serializers
from analytics.serializers.common import DateRangeSerializer, FilterSerializer
from analytics.utils.helpers import TRUNC_MAP


class PerformanceAnalyticsRequestSerializer(DateRangeSerializer, FilterSerializer):
    """Request serializer for performance analytics."""
    compare = serializers.ChoiceField(
        choices=list(TRUNC_MAP.keys()),
        default="month",
        help_text="Period size for comparison"
    )
    user_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Optional user ID to filter by specific user"
    )

    class Meta:
        fields = ["compare", "user_id", "filters", "start", "end"]


class PerformanceAnalyticsResponseSerializer(serializers.Serializer):
    """Response serializer for performance analytics."""
    x = serializers.CharField(help_text="Period label with blog count")
    y = serializers.IntegerField(help_text="Views in period")
    z = serializers.FloatField(
        allow_null=True,
        help_text="Growth percentage vs previous period"
    )

