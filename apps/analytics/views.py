from __future__ import annotations
from typing import Any, Dict, List, Tuple

from django.db.models import Count, Sum, F, Q, Value
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek, TruncDay, TruncYear
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from .models import Blog, BlogView, User, Country
from .utils.filters import build_q_from_filter


# Helper: choose truncation function
TRUNC_MAP = {
    "month": TruncMonth,
    "week": TruncWeek,
    "day": TruncDay,
    "year": TruncYear,
}


def parse_timerange(qs, start: str | None, end: str | None, datetime_field: str = "viewed_at"):
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


class BlogViewsAnalyticsView(APIView):
    """
    /analytics/blog-views/
    - object_type: 'country' | 'user'
    - range: 'month'|'week'|'year'|'day'
    - filters: JSON filter object (dynamic filters)
    Response:
      [
        { "x": "<grouping key>", "y": number_of_blogs, "z": total_views },
        ...
      ]
    Aggregation:
      group blogs (distinct blog count) and total views per grouping key.
    """
    def post(self, request: Request) -> Response:  # type: ignore[override]
        payload = request.data
        object_type = payload.get("object_type", "country")
        time_range = payload.get("range")  # optional
        filters = payload.get("filters")  # optional, dynamic filter tree
        start = payload.get("start")  # ISO date
        end = payload.get("end")

        # Base queryset: join Blog and BlogView
        # We want: group by object_type value, count distinct blogs, sum views rows
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        # Apply dynamic filters if provided
        if filters:
            q = build_q_from_filter(filters)
            # filters may refer to fields from Blog, BlogView, User, Country; Q handles double-underscore
            view_qs = view_qs.filter(q)

        # Apply time range to the view timestamp
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        # Decide grouping key
        if object_type == "user":
            # group by blog author
            # annotate author username or id as x, number of distinct blogs y, z total views
            agg_qs = (
                view_qs
                .values(author_username=F("blog__author__username"), author_id=F("blog__author__id"))
                .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
                .order_by("-total_views")
            )
            # Map to expected x,y,z
            result = [
                {"x": f"{r['author_username']} ({r['author_id']})", "y": r["number_of_blogs"], "z": r["total_views"]}
                for r in agg_qs
            ]
            return Response(result)

        # default: country
        agg_qs = (
            view_qs
            .values(country_code=F("blog__country__code"), country_name=F("blog__country__name"))
            .annotate(number_of_blogs=Count("blog", distinct=True), total_views=Count("id"))
            .order_by("-total_views")
        )
        result = [
            {"x": f"{r['country_name'] or r['country_code']}", "y": r["number_of_blogs"], "z": r["total_views"]}
            for r in agg_qs
        ]
        return Response(result)


class TopAnalyticsView(APIView):
    """
    /analytics/top/
    - top: 'user'|'country'|'blog'
    - time range fields: start, end (ISO)
    - filters: dynamic filter tree
    Returns top 10 by total views. x,y,z vary per 'top' selection.
    """
    def post(self, request: Request) -> Response:  # type: ignore[override]
        payload = request.data
        top = payload.get("top", "blog")
        filters = payload.get("filters")
        start = payload.get("start")
        end = payload.get("end")

        view_qs = BlogView.objects.select_related("blog__author", "blog__country")

        if filters:
            view_qs = view_qs.filter(build_q_from_filter(filters))
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")

        # Annotate totals per requested top
        if top == "user":
            qs = (
                view_qs
                .values(user_id=F("blog__author__id"), user_name=F("blog__author__username"))
                .annotate(total_views=Count("id"), blogs_count=Count("blog", distinct=True))
                .order_by("-total_views")[:10]
            )
            result = [
                {"x": r["user_name"], "y": r["blogs_count"], "z": r["total_views"]}
                for r in qs
            ]
            return Response(result)

        if top == "country":
            qs = (
                view_qs
                .values(country_code=F("blog__country__code"), country_name=F("blog__country__name"))
                .annotate(total_views=Count("id"), blogs_count=Count("blog", distinct=True))
                .order_by("-total_views")[:10]
            )
            result = [
                {"x": r["country_name"] or r["country_code"], "y": r["blogs_count"], "z": r["total_views"]}
                for r in qs
            ]
            return Response(result)

        # default: blog
        qs = (
            view_qs
            .values(blog_id=F("blog__id"), blog_title=F("blog__title"))
            .annotate(total_views=Count("id"))
            .order_by("-total_views")[:10]
        )
        result = [
            {"x": r["blog_title"], "y": r["blog_id"], "z": r["total_views"]} for r in qs
        ]
        return Response(result)


class PerformanceAnalyticsView(APIView):
    """
    /analytics/performance/
    - compare: 'month'|'week'|'day'|'year' (period size)
    - user_id optional (if provided, performance for single user; otherwise all users)
    - filters: dynamic filters applied before aggregation
    Response per period:
      { "x": "<period label> (n_blogs)", "y": views_in_period, "z": growth_pct_vs_previous_period }
    Implementation notes:
      - We count blog creations in the period (number_of_blogs).
      - We sum views within the same period.
      - Growth is computed relative to previous period's views; when previous = 0 use None or 100%.
    """
    def post(self, request: Request) -> Response:  # type: ignore[override]
        payload = request.data
        compare = payload.get("compare", "month")
        if compare not in TRUNC_MAP:
            return Response({"detail": "invalid compare"}, status=status.HTTP_400_BAD_REQUEST)
        filters = payload.get("filters")
        user_id = payload.get("user_id")
        start = payload.get("start")
        end = payload.get("end")

        trunc_func = TRUNC_MAP[compare]

        # Base view queryset for counting views
        view_qs = BlogView.objects.select_related("blog__author", "blog__country")
        blog_qs = Blog.objects.select_related("author", "country")

        # Apply filters to both view and blog querysets.
        # Filters may refer to blog fields (created_at) or view fields (viewed_at).
        if filters:
            q = build_q_from_filter(filters)
            # Apply to both querysets; some lookups won't match but that's ok.
            view_qs = view_qs.filter(q)
            blog_qs = blog_qs.filter(q)

        # Time range filters if present
        view_qs = parse_timerange(view_qs, start, end, datetime_field="viewed_at")
        blog_qs = parse_timerange(blog_qs, start, end, datetime_field="created_at")

        if user_id:
            view_qs = view_qs.filter(blog__author__id=user_id)
            blog_qs = blog_qs.filter(author__id=user_id)

        # Aggregate views by period
        # First annotate each view's period
        view_agg = (
            view_qs
            .annotate(period=trunc_func("viewed_at"))
            .values("period")
            .annotate(views_in_period=Count("id"))
            .order_by("period")
        )

        # Count blogs created per period
        blog_agg = (
            blog_qs
            .annotate(period=trunc_func("created_at"))
            .values("period")
            .annotate(blogs_in_period=Count("id"))
            .order_by("period")
        )

        # Convert to dict for quick lookup; avoid N+1 and extra DB hits
        views_map = {row["period"]: row["views_in_period"] for row in view_agg}
        blogs_map = {row["period"]: row["blogs_in_period"] for row in blog_agg}

        # Build sorted list of periods (union of periods)
        all_periods = sorted(set(views_map.keys()) | set(blogs_map.keys()))

        # Compute growth vs previous period
        result: List[Dict[str, Any]] = []
        prev_views = None
        for period in all_periods:
            views = safe_int(views_map.get(period, 0))
            blogs_count = safe_int(blogs_map.get(period, 0))
            if prev_views is None:
                growth = None
            else:
                if prev_views == 0:
                    growth = None if views == 0 else 100.0
                else:
                    growth = (views - prev_views) / prev_views * 100.0
            prev_views = views
            # label period -> str(period) is localized UTC timestamp; convert to isoformat for clarity
            label = f"{period.isoformat()} ({blogs_count} blogs)"
            result.append({"x": label, "y": views, "z": (round(growth, 2) if growth is not None else None)})

        return Response(result)
