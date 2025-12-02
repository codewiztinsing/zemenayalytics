"""
Management command to set up Celery Beat periodic tasks.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from analytics.tasks import (
    aggregate_blog_views_hourly,
    aggregate_blog_views_daily,
    aggregate_blog_views_weekly,
    aggregate_blog_views_monthly,
    aggregate_blog_views_yearly,
    aggregate_blog_creations_daily,
    aggregate_blog_creations_monthly,
    aggregate_blog_creations_yearly,
)


class Command(BaseCommand):
    help = "Set up Celery Beat periodic tasks for time series aggregation"

    def handle(self, *args, **options):
        self.stdout.write("Setting up Celery Beat periodic tasks...")

        # Create interval schedules
        hourly_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        daily_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        # Create crontab schedules
        weekly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=0,
            day_of_week=0,  # Sunday
        )

        monthly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=0,
            day_of_month=1,  # First day of month
        )

        yearly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=0,
            day_of_month=1,
            month_of_year=1,  # January
        )

        # Blog Views Aggregation Tasks
        tasks = [
            {
                "name": "Aggregate Blog Views - Hourly",
                "task": "analytics.tasks.aggregation.aggregate_blog_views_hourly",
                "schedule": hourly_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Views - Daily",
                "task": "analytics.tasks.aggregation.aggregate_blog_views_daily",
                "schedule": daily_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Views - Weekly",
                "task": "analytics.tasks.aggregation.aggregate_blog_views_weekly",
                "schedule": weekly_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Views - Monthly",
                "task": "analytics.tasks.aggregation.aggregate_blog_views_monthly",
                "schedule": monthly_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Views - Yearly",
                "task": "analytics.tasks.aggregation.aggregate_blog_views_yearly",
                "schedule": yearly_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Creations - Daily",
                "task": "analytics.tasks.aggregation.aggregate_blog_creations_daily",
                "schedule": daily_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Creations - Monthly",
                "task": "analytics.tasks.aggregation.aggregate_blog_creations_monthly",
                "schedule": monthly_schedule,
                "enabled": True,
            },
            {
                "name": "Aggregate Blog Creations - Yearly",
                "task": "analytics.tasks.aggregation.aggregate_blog_creations_yearly",
                "schedule": yearly_schedule,
                "enabled": True,
            },
        ]

        created_count = 0
        updated_count = 0

        for task_config in tasks:
            task, created = PeriodicTask.objects.update_or_create(
                name=task_config["name"],
                defaults={
                    "task": task_config["task"],
                    "interval": task_config["schedule"] if isinstance(task_config["schedule"], IntervalSchedule) else None,
                    "crontab": task_config["schedule"] if isinstance(task_config["schedule"], CrontabSchedule) else None,
                    "enabled": task_config["enabled"],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created periodic task: {task_config['name']}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated periodic task: {task_config['name']}"))

        self.stdout.write(self.style.SUCCESS(f"\nCompleted! Created: {created_count}, Updated: {updated_count}"))

