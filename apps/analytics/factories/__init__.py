"""
Analytics app factories for generating test data.
"""
from apps.analytics.factories.country import CountryFactory
from apps.analytics.factories.blog import BlogFactory
from apps.analytics.factories.blog_view import BlogViewFactory

__all__ = [
    "CountryFactory",
    "BlogFactory",
    "BlogViewFactory",
]

