"""
Factory for Country model.
"""
import factory
from analytics.models import Country


def get_next_country_code():
    """Get the next available country code."""
    # Get the highest numeric code from existing countries
    # Find all codes that start with "CO" and extract the number
    existing_codes = Country.objects.filter(code__startswith='CO').values_list('code', flat=True)
    max_num = -1
    for code in existing_codes:
        try:
            # Extract number from "CO###" format
            if len(code) > 2 and code[2:].isdigit():
                num = int(code[2:])
                max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue
    return f"CO{max_num + 1:03d}"


class CountryFactory(factory.django.DjangoModelFactory):
    """Factory for creating Country instances."""
    
    class Meta:
        model = Country
    
    code = factory.LazyFunction(get_next_country_code)
    name = factory.Faker("country")
    continent = factory.Faker("random_element", elements=[
        "Africa", "Asia", "Europe", "North America", 
        "South America", "Oceania", "Antarctica"
    ])

