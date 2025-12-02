"""
Serializers for Blog Views Analytics endpoint.
"""
from rest_framework import serializers
from analytics.serializers.common import DateRangeSerializer, FilterSerializer


class BlogViewsAnalyticsRequestSerializer(DateRangeSerializer, FilterSerializer):
    """Request serializer for blog views analytics."""
    object_type = serializers.ChoiceField(
        choices=["country", "user"],
        default="country",
        help_text="Group by country or user"
    )

    class Meta:
        fields = ["object_type", "filters", "start", "end"]


class BlogViewsAnalyticsResponseSerializer(serializers.Serializer):
    """Response serializer for blog views analytics."""
    x = serializers.CharField(help_text="Grouping key with time period (e.g., 'Ethiopia - 2024-01' or 'username (id) - 2024-01')")
    y = serializers.IntegerField(help_text="Number of distinct blogs")
    z = serializers.IntegerField(help_text="Total views")

