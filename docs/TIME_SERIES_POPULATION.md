# Time Series Data Population Guide

## Overview

The time series aggregates need to be populated from existing `BlogView` and `Blog` data. There are two ways to populate them:

1. **Backfill Command** - Populates historical data all at once
2. **Celery Tasks** - Automatically aggregates new data on a schedule

## Quick Start

### Option 1: Backfill All Historical Data (Recommended for Initial Setup)

Backfill all granularities from all existing data:

```bash
docker compose exec dev python manage.py backfill_time_series
```

This will:
- Process all historical data
- Create aggregates for all granularities (hour, day, week, month, year)
- Show progress for each granularity

### Option 2: Backfill Specific Granularity

Backfill only daily aggregates:

```bash
docker compose exec dev python manage.py backfill_time_series --granularity day
```

Available granularities: `hour`, `day`, `week`, `month`, `year`, `all`

### Option 3: Backfill Date Range

Backfill data for a specific date range:

```bash
docker compose exec dev python manage.py backfill_time_series --start-date 2025-01-01 --end-date 2025-01-31
```

### Option 4: Clear and Rebuild

Clear existing aggregates and rebuild from scratch:

```bash
docker compose exec dev python manage.py backfill_time_series --clear
```

## Command Options

```
--granularity {hour,day,week,month,year,all}
    Granularity to backfill (default: all)

--start-date YYYY-MM-DD
    Start date for backfilling. If not provided, uses earliest data.

--end-date YYYY-MM-DD
    End date for backfilling. If not provided, uses current date.

--clear
    Clear existing aggregates for the specified granularity before backfilling
```

## Automatic Population (Celery Beat)

Once set up, Celery Beat will automatically aggregate new data:

1. **Set up Celery Beat schedules:**
   ```bash
   docker compose exec dev python manage.py setup_celery_beat
   ```

2. **Start Celery services:**
   ```bash
   docker compose up celery_worker celery_beat
   ```

The scheduled tasks will:
- **Hourly**: Aggregate previous hour's blog views
- **Daily**: Aggregate previous day's blog views and creations
- **Weekly**: Aggregate previous week's data (runs on Sunday)
- **Monthly**: Aggregate previous month's data (runs on 1st of month)
- **Yearly**: Aggregate previous year's data (runs on January 1st)

## Manual Task Execution

You can also manually trigger aggregation tasks:

```bash
# Using Django shell
docker compose exec dev python manage.py shell
```

```python
from apps.analytics.tasks import (
    aggregate_blog_views_daily,
    aggregate_blog_creations_daily,
)

# Execute tasks synchronously
aggregate_blog_views_daily()
aggregate_blog_creations_daily()
```

Or using Celery:

```bash
docker compose exec celery_worker celery -A config call apps.analytics.tasks.time_series_aggregation.aggregate_blog_views_daily
```

## Verification

Check if aggregates are populated:

```bash
docker compose exec dev python manage.py shell
```

```python
from apps.analytics.models.time_series_aggregate import (
    BlogViewTimeSeriesAggregate,
    BlogCreationTimeSeriesAggregate,
    TimeSeriesGranularity,
)

# Count aggregates by granularity
for gran in TimeSeriesGranularity.choices:
    count = BlogViewTimeSeriesAggregate.objects.filter(granularity=gran[0]).count()
    print(f"{gran[1]}: {count} aggregates")

# Check blog creation aggregates
for gran in TimeSeriesGranularity.choices:
    count = BlogCreationTimeSeriesAggregate.objects.filter(granularity=gran[0]).count()
    print(f"{gran[1]}: {count} aggregates")
```

## Troubleshooting

### No aggregates after backfill

1. Check if you have data:
   ```bash
   docker compose exec dev python manage.py shell
   ```
   ```python
   from apps.analytics.models import BlogView, Blog
   print(f"BlogViews: {BlogView.objects.count()}")
   print(f"Blogs: {Blog.objects.count()}")
   ```

2. Check for errors in the backfill output

3. Verify the date range covers your data

### Performance issues with large datasets

For very large datasets, backfill specific granularities one at a time:

```bash
# Backfill daily first (most commonly used)
docker compose exec dev python manage.py backfill_time_series --granularity day

# Then backfill weekly/monthly/yearly (these can aggregate from daily)
docker compose exec dev python manage.py backfill_time_series --granularity week
docker compose exec dev python manage.py backfill_time_series --granularity month
docker compose exec dev python manage.py backfill_time_series --granularity year
```

## Next Steps

After populating the aggregates:

1. Verify the data is correct
2. Set up Celery Beat for ongoing aggregation
3. Test the `/analytics/performance/` endpoint to ensure it returns data

