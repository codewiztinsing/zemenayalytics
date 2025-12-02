"""
Helper functions and constants shared across analytics views and services.
"""
import json
from typing import Any
from django.http import QueryDict
from django.db.models import QuerySet
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, TruncYear
from config.logger import logger


# Helper: choose truncation function
TRUNC_MAP = {
    "month": TruncMonth,
    "week": TruncWeek,
    "day": TruncDay,
    "year": TruncYear,
}


def parse_timerange(qs: QuerySet, start: str | None, end: str | None, datetime_field: str = "viewed_at") -> QuerySet:
    """
    Apply a time range filter to a queryset. start/end should be ISO date strings
    (YYYY-MM-DD) or None.
    """
    if start:
        qs = qs.filter(**{f"{datetime_field}__gte": start})
    if end:
        qs = qs.filter(**{f"{datetime_field}__lte": end})
    return qs


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int, returning default if conversion fails."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def parse_query_params(query_params: QueryDict) -> dict[str, Any]:
    """
    Convert DRF QueryDict to a regular dict, handling list values,
    empty strings, and JSON parsing for filters.
    
    Args:
        query_params: QueryDict from request.query_params
        
    Returns:
        dict: Regular dictionary with parsed query parameters
    """
    data = {}
    for key, value in query_params.items():
        logger.debug(f"Query parameter - Key: {key}, Value: {value}")
        # QueryDict returns lists, get the first element
        if isinstance(value, list):
            value = value[0] if value else None
        # Convert empty strings to None for optional fields
        if value == "":
            value = None
        data[key] = value
    
    # Parse filters from JSON string if provided
    if "filters" in data and data["filters"]:
        try:
            # Parse JSON string to dict
            data["filters"] = json.loads(data["filters"])
            logger.debug(f"Parsed filters: {data['filters']}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse filters JSON: {e}")
            # If it's not valid JSON, pass it as-is and let serializer handle validation
            pass
    
    logger.debug(f"Parsed query params: {data}")
    return data

