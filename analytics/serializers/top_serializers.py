"""
Serializers for Top Analytics endpoint.
"""
from rest_framework import serializers
from analytics.serializers.common import DateRangeSerializer, FilterSerializer


class TopAnalyticsRequestSerializer(DateRangeSerializer, FilterSerializer):
    """Request serializer for top analytics."""
    top = serializers.ChoiceField(
        choices=["user", "country", "blog"],
        default="blog",
        help_text="Type of top analytics to retrieve"
    )

    class Meta:
        fields = ["top", "filters", "start", "end"]


class TopAnalyticsResponseSerializer(serializers.Serializer):
    """Response serializer for top analytics."""
    x = serializers.CharField(help_text="Name/title (varies by top type)")
    y = serializers.IntegerField(help_text="Blogs count or blog ID (varies by top type)")
    z = serializers.IntegerField(help_text="Total views")

