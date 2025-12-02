"""
Factory for Blog model.
"""
import factory
from django.contrib.auth.models import User
from analytics.models import Blog, Country, Author,BlogView


class BlogFactory(factory.django.DjangoModelFactory):
    """Factory for creating Blog instances."""
    
    class Meta:
        model = Blog
    
    title = factory.Faker("sentence", nb_words=6)
    author = factory.LazyAttribute(
        lambda obj: Author.objects.order_by("?").first() if Author.objects.exists() else None
    )
    country = factory.LazyAttribute(
        lambda obj: Country.objects.order_by("?").first() if Country.objects.exists() else None
    )




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


