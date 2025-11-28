from django.db import models
from django.contrib.auth.models import User
from .country import Country


class Blog(models.Model):
    """
    Blog/post model. Key fields used by analytics: author, country, created_at.
    """
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, related_name="blogs", on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_author_name(self):
        return f"{self.author.first_name} {self.author.last_name}"

    class Meta:
        verbose_name = "Blog"
        verbose_name_plural = "Blogs"
        ordering = ["-created_at"]

