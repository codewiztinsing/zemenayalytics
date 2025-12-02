"""
Analytics app models.

Each model is defined in its own module for better organization.
"""
from .country import Country
from .blog import Blog, BlogView
from .author import Author
from .aggregation import (
    TimeSeriesGranularity,
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
)

__all__ = [
    "Country",
    "Blog",
    "BlogView",
    "Author",
    "TimeSeriesGranularity",
    "BlogViewTimeSeriesAggregate",
    "BlogCreationTimeSeriesAggregate",
]

