# analytics/utils/filters.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union

from django.db.models import Q


FilterDict = Dict[str, Any]


def build_q_from_filter(filter_obj: FilterDict) -> Q:
    """
    Convert a filter object (JSON-friendly) into a Django Q object.

    Supported operators:
      - "and": [filter, ...]
      - "or": [filter, ...]
      - "not": filter
      - "eq": {"field": "author.username", "value": "alice"}
      - "lt", "lte", "gt", "gte", "contains", "in"

    Examples:
      {"and": [
         {"eq": {"field": "author.country.code", "value": "ET"}},
         {"or": [
             {"gte": {"field": "created_at", "value": "2025-01-01"}},
             {"lt": {"field": "created_at", "value": "2024-01-01"}}
          ]}
      ]}

    This function supports multi-table lookups through dot notation: "author.country.code"
    which will be converted to Django "__" lookups.
    """
    if not isinstance(filter_obj, dict):
        raise ValueError("filter_obj must be a dict")

    # Logical combinators:
    if "and" in filter_obj:
        children = filter_obj["and"]
        if not isinstance(children, list):
            raise ValueError("and must be a list")
        q = Q()
        for child in children:
            q &= build_q_from_filter(child)
        return q

    if "or" in filter_obj:
        children = filter_obj["or"]
        if not isinstance(children, list):
            raise ValueError("or must be a list")
        q = Q()
        for child in children:
            q |= build_q_from_filter(child)
        return q

    if "not" in filter_obj:
        child = filter_obj["not"]
        return ~build_q_from_filter(child)

    # Comparison operators:
    comp_ops = ("eq", "lt", "lte", "gt", "gte", "contains", "in")
    for op in comp_ops:
        if op in filter_obj:
            payload = filter_obj[op]
            if not isinstance(payload, dict):
                raise ValueError(f"{op} payload must be a dict")
            field = payload.get("field")
            value = payload.get("value")
            if field is None:
                raise ValueError(f"{op} requires a 'field' key")
            django_lookup = field.replace(".", "__")
            if op == "eq":
                lookup = f"{django_lookup}"
                return Q(**{lookup: value})
            if op == "in":
                lookup = f"{django_lookup}__in"
                if not isinstance(value, list):
                    raise ValueError("in expects a list value")
                return Q(**{lookup: value})
            if op == "contains":
                lookup = f"{django_lookup}__icontains"
                return Q(**{lookup: value})
            # numeric/comparable
            lookup = f"{django_lookup}__{op}"
            return Q(**{lookup: value})

    raise ValueError(f"Unsupported filter: {filter_obj}")
