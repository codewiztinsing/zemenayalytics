"""
Helper functions and constants shared across analytics views.
"""
from typing import Any
from django.db.models import QuerySet
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, TruncYear


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
    (YYYY-MM-DD or full ISO). Returns filtered queryset.
    """
    if start:
        qs = qs.filter(**{f"{datetime_field}__gte": start})
    if end:
        qs = qs.filter(**{f"{datetime_field}__lte": end})
    return qs


def safe_int(val: Any, default: int = 0) -> int:
    """Small helper to coerce to int."""
    try:
        return int(val)
    except Exception:
        return default

