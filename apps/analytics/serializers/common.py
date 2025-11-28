"""
Common serializers and fields used across multiple analytics endpoints.
"""
from rest_framework import serializers


class DateRangeSerializer(serializers.Serializer):
    """Common date range fields for filtering."""
    start = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Start date in ISO format (YYYY-MM-DD)"
    )
    end = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="End date in ISO format (YYYY-MM-DD)"
    )

    def validate(self, attrs):
        """Validate that start date is before end date."""
        start = attrs.get("start")
        end = attrs.get("end")
        
        if start and end and start > end:
            raise serializers.ValidationError({
                "end": "End date must be after start date."
            })
        
        return attrs


class FilterSerializer(serializers.Serializer):
    """Dynamic filter tree serializer."""
    filters = serializers.DictField(
        required=False,
        allow_null=True,
        help_text="Dynamic filter tree (optional)"
    )


class AnalyticsDataPointSerializer(serializers.Serializer):
    """Common response data point structure."""
    x = serializers.CharField(help_text="Grouping key or label")
    y = serializers.IntegerField(help_text="Count or metric value")
    z = serializers.IntegerField(help_text="Total views or secondary metric")

