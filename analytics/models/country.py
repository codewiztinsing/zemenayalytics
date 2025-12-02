from django.db import models
from analytics.utils.base import BaseModel 


class Country(BaseModel):
    """
    Simple Country model used in examples.
    """
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=128)
    continent = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    def get_code_and_name(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

