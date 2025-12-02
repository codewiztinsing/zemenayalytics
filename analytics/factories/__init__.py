"""
Analytics app factories for generating test data.
"""
from analytics.factories.country_factories import CountryFactory
from analytics.factories.blog_factories import BlogFactory,BlogViewFactory

__all__ = [
    "CountryFactory",
    "BlogFactory",
    "BlogViewFactory",
]

