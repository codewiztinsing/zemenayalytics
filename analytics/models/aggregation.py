"""
Time Series Aggregate Models for Compressive Time Series Storage.

These models store aggregated time series data at different granularities:
- raw: Individual records (for recent data only)
- hour: Hourly aggregates
- day: Daily aggregates
- week: Weekly aggregates
- month: Monthly aggregates
- year: Yearly aggregates
"""
from django.db import models
from .blog import Blog
from .country import Country
from .author import Author


class TimeSeriesGranularity(models.TextChoices):
    """Granularity levels for time series aggregation."""
    RAW = "raw", "Raw"
    HOUR = "hour", "Hour"
    DAY = "day", "Day"
    WEEK = "week", "Week"
    MONTH = "month", "Month"
    YEAR = "year", "Year"


class BlogViewTimeSeriesAggregate(models.Model):
    """
    Aggregated time series data for Blog views.
    Stores counts and metrics at different time granularities.
    """
    # Time and granularity
    granularity = models.CharField(
        max_length=10,
        choices=TimeSeriesGranularity.choices,
        db_index=True,
        help_text="Time granularity level (raw, hour, day, week, month, year)"
    )
    time_bucket = models.DateTimeField(
        db_index=True,
        help_text="The start time of the aggregation bucket"
    )
    
    # Relationships (optional, for filtering)
    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="view_time_series_aggregates",
        help_text="Specific blog (null for all blogs aggregate)"
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="view_time_series_aggregates",
        help_text="Specific country (null for all countries aggregate)"
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="view_time_series_aggregates",
        help_text="Specific author (null for all authors aggregate)"
    )
    
    # Aggregated metrics
    view_count = models.IntegerField(
        default=0,
        help_text="Total number of views in this time bucket"
    )
    unique_blogs_viewed = models.IntegerField(
        default=0,
        help_text="Number of distinct blogs viewed in this time bucket"
    )
    unique_users = models.IntegerField(
        default=0,
        help_text="Number of distinct users who viewed in this time bucket"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Blog View Time Series Aggregate"
        verbose_name_plural = "Blog View Time Series Aggregates"
        ordering = ["-time_bucket", "granularity"]
        # Unique constraint to prevent duplicate aggregates
        unique_together = [
            ["granularity", "time_bucket", "blog", "country", "author"]
        ]
        indexes = [
            models.Index(fields=["granularity", "time_bucket"]),
            models.Index(fields=["time_bucket", "granularity"]),
            models.Index(fields=["blog", "granularity", "time_bucket"]),
            models.Index(fields=["country", "granularity", "time_bucket"]),
            models.Index(fields=["author", "granularity", "time_bucket"]),
        ]
    
    def __str__(self):
        blog_str = f" - {self.blog.title}" if self.blog else ""
        country_str = f" - {self.country.name}" if self.country else ""
        return f"{self.granularity} - {self.time_bucket}{blog_str}{country_str} - {self.view_count} views"


class BlogCreationTimeSeriesAggregate(models.Model):
    """
    Aggregated time series data for Blog creation metrics.
    Stores blog creation counts at different time granularities.
    """
    # Time and granularity
    granularity = models.CharField(
        max_length=10,
        choices=TimeSeriesGranularity.choices,
        db_index=True,
        help_text="Time granularity level (raw, hour, day, week, month, year)"
    )
    time_bucket = models.DateTimeField(
        db_index=True,
        help_text="The start time of the aggregation bucket"
    )
    
    # Relationships (optional, for filtering)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_creation_aggregates",
        help_text="Specific country (null for all countries aggregate)"
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="blog_creation_aggregates",
        help_text="Specific author (null for all authors aggregate)"
    )
    
    # Aggregated metrics
    blog_count = models.IntegerField(
        default=0,
        help_text="Number of blogs created in this time bucket"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Blog Creation Time Series Aggregate"
        verbose_name_plural = "Blog Creation Time Series Aggregates"
        ordering = ["-time_bucket", "granularity"]
        # Unique constraint to prevent duplicate aggregates
        unique_together = [
            ["granularity", "time_bucket", "country", "author"]
        ]
        indexes = [
            models.Index(fields=["granularity", "time_bucket"]),
            models.Index(fields=["time_bucket", "granularity"]),
            models.Index(fields=["country", "granularity", "time_bucket"]),
            models.Index(fields=["author", "granularity", "time_bucket"]),
        ]
    
    def __str__(self):
        country_str = f" - {self.country.name}" if self.country else ""
        return f"{self.granularity} - {self.time_bucket}{country_str} - {self.blog_count} blogs"
