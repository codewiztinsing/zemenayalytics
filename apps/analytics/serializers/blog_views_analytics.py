"""
Serializers for Blog Views Analytics endpoint.
"""
from rest_framework import serializers
from apps.analytics.serializers.common import DateRangeSerializer, FilterSerializer


class BlogViewsAnalyticsRequestSerializer(DateRangeSerializer, FilterSerializer):
    """Request serializer for blog views analytics."""
    object_type = serializers.ChoiceField(
        choices=["country", "user"],
        default="country",
        help_text="Group by country or user"
    )
    range = serializers.ChoiceField(
        choices=["month", "week", "year", "day"],
        required=False,
        allow_null=True,
        help_text="Time range for aggregation (optional)"
    )

    class Meta:
        fields = ["object_type", "range", "filters", "start", "end"]


class BlogViewsAnalyticsResponseSerializer(serializers.Serializer):
    """Response serializer for blog views analytics."""
    x = serializers.CharField(help_text="Grouping key (country name or user)")
    y = serializers.IntegerField(help_text="Number of distinct blogs")
    z = serializers.IntegerField(help_text="Total views")

