"""
Factory for Blog model.
"""
import factory
from django.contrib.auth.models import User
from apps.analytics.models import Blog, Country


class BlogFactory(factory.django.DjangoModelFactory):
    """Factory for creating Blog instances."""
    
    class Meta:
        model = Blog
    
    title = factory.Faker("sentence", nb_words=6)
    author = factory.LazyAttribute(
        lambda obj: User.objects.order_by("?").first() if User.objects.exists() else None
    )
    country = factory.LazyAttribute(
        lambda obj: Country.objects.order_by("?").first() if Country.objects.exists() else None
    )

