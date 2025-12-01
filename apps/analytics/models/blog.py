from django.db import models
from django.contrib.auth.models import User
from apps.analytics.utils.base import BaseModel
from .country import Country
from .author import Author


class Blog(BaseModel):
    """
    Blog/post model. Key fields used by analytics: author, country, created_at.
    """
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, related_name="blogs", on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

    def get_author_name(self):
        return f"{self.author.user.first_name} {self.author.user.last_name}"

    class Meta:
        verbose_name = "Blog"
        verbose_name_plural = "Blogs"
        ordering = ["-created_at"]

