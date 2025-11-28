"""
Factory for Country model.
"""
import factory
from apps.analytics.models import Country


class CountryFactory(factory.django.DjangoModelFactory):
    """Factory for creating Country instances."""
    
    class Meta:
        model = Country
    
    code = factory.Sequence(lambda n: f"CO{n:03d}")
    name = factory.Faker("country")
    continent = factory.Faker("random_element", elements=[
        "Africa", "Asia", "Europe", "North America", 
        "South America", "Oceania", "Antarctica"
    ])

