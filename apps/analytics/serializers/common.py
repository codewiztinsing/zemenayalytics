"""
Common serializers and fields used across multiple analytics endpoints.
"""
from rest_framework import serializers
from typing import Any, Dict


def validate_filter_structure(filter_obj: Any) -> None:
    """
    Validate that a filter object matches the expected structure.
    
    Supported operators:
    - "and": [filter, ...]
    - "or": [filter, ...]
    - "not": filter
    - "eq", "lt", "lte", "gt", "gte", "contains", "in": {"field": "...", "value": ...}
    
    Raises:
        ValueError: If the filter structure is invalid
    """
    if filter_obj is None:
        return
    
    if not isinstance(filter_obj, dict):
        raise ValueError("Filter must be a dictionary")
    
    # Check for logical operators
    logical_ops = ["and", "or", "not"]
    has_logical_op = any(op in filter_obj for op in logical_ops)
    
    # Check for comparison operators
    comp_ops = ["eq", "lt", "lte", "gt", "gte", "contains", "in"]
    has_comp_op = any(op in filter_obj for op in comp_ops)
    
    # Filter must have exactly one operator
    if not (has_logical_op or has_comp_op):
        # Check if it looks like Swagger's additionalProp pattern
        if any(key.startswith("additionalProp") for key in filter_obj.keys()):
            raise ValueError(
                "Invalid filter format. Filters must use operators like 'eq', 'and', 'or', etc. "
                "Example: {'eq': {'field': 'blog.country.code', 'value': 'US'}}"
            )
        raise ValueError(
            f"Invalid filter format. Filter must contain one of: {logical_ops + comp_ops}. "
            f"Received keys: {list(filter_obj.keys())}"
        )
    
    # Validate logical operators
    if "and" in filter_obj:
        children = filter_obj["and"]
        if not isinstance(children, list):
            raise ValueError("'and' operator must have a list value")
        if len(children) == 0:
            raise ValueError("'and' operator must have at least one filter")
        for child in children:
            validate_filter_structure(child)
    
    if "or" in filter_obj:
        children = filter_obj["or"]
        if not isinstance(children, list):
            raise ValueError("'or' operator must have a list value")
        if len(children) == 0:
            raise ValueError("'or' operator must have at least one filter")
        for child in children:
            validate_filter_structure(child)
    
    if "not" in filter_obj:
        validate_filter_structure(filter_obj["not"])
    
    # Validate comparison operators
    for op in comp_ops:
        if op in filter_obj:
            payload = filter_obj[op]
            if not isinstance(payload, dict):
                raise ValueError(f"'{op}' operator must have a dictionary value with 'field' and 'value' keys")
            if "field" not in payload:
                raise ValueError(f"'{op}' operator requires a 'field' key")
            if "value" not in payload:
                raise ValueError(f"'{op}' operator requires a 'value' key")
            
            # Validate 'in' operator requires a list value
            if op == "in" and not isinstance(payload.get("value"), list):
                raise ValueError(f"'{op}' operator requires 'value' to be a list")


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
        help_text="Dynamic filter tree (optional). Supported operators: eq, lt, lte, gt, gte, contains, in, and, or, not. Example: {'eq': {'field': 'blog.country.code', 'value': 'US'}}"
    )
    
    def validate_filters(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the filter structure.
        
        Raises:
            serializers.ValidationError: If the filter structure is invalid
        """
        if value is None:
            return value
        
        try:
            validate_filter_structure(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        
        return value


class AnalyticsDataPointSerializer(serializers.Serializer):
    """Common response data point structure."""
    x = serializers.CharField(help_text="Grouping key or label")
    y = serializers.IntegerField(help_text="Count or metric value")
    z = serializers.IntegerField(help_text="Total views or secondary metric")

