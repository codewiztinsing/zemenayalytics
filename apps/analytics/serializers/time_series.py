"""
Serializers for Time Series Analytics endpoint.
"""
from rest_framework import serializers
from apps.analytics.serializers.common import DateRangeSerializer, FilterSerializer


class TimeSeriesRequestSerializer(DateRangeSerializer, FilterSerializer):
    """Request serializer for time series analytics."""
    granularity = serializers.ChoiceField(
        choices=["day", "week", "month", "year"],
        default="day",
        help_text="Time granularity for aggregation"
    )

    class Meta:
        fields = ["granularity", "filters", "start", "end"]


class TimeSeriesResponseSerializer(serializers.Serializer):
    """Response serializer for time series analytics."""
    x = serializers.CharField(help_text="Time period (ISO format)")
    y = serializers.IntegerField(help_text="View count for the period")
    z = serializers.IntegerField(help_text="Number of unique blogs viewed in the period")

