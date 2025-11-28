"""
Factory for BlogView model.
"""
import factory
from django.contrib.auth.models import User
from apps.analytics.models import BlogView, Blog
from datetime import timedelta, datetime
import random


class BlogViewFactory(factory.django.DjangoModelFactory):
    """Factory for creating BlogView instances."""
    
    class Meta:
        model = BlogView
    
    blog = factory.LazyAttribute(
        lambda obj: Blog.objects.order_by("?").first() if Blog.objects.exists() else None
    )
    user = factory.LazyAttribute(
        lambda obj: (
            User.objects.order_by("?").first() 
            if User.objects.exists() and random.random() > 0.3 
            else None
        )
    )
    viewed_at = factory.Faker("date_time_between", start_date="-1y", end_date="now")

