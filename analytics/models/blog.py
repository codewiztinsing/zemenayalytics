from django.db import models
from django.contrib.auth.models import User
from analytics.utils.base import BaseModel
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



class BlogView(BaseModel):
    """
    Each record represents a view of a blog.
    We aggregate counts of these rows to compute 'views'.
    """
    blog = models.ForeignKey(Blog, related_name="views", on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Viewed {self.blog.title} by {self.user.get_full_name()}"
        return f"Viewed {self.blog.title} by anonymous"

    def get_viewed_at_date(self):
        return self.viewed_at.date()

    def get_viewed_at_time(self):
        return self.viewed_at.time()

    def get_viewed_at_datetime(self):
        return self.viewed_at

    class Meta:
        verbose_name = "Blog View"
        verbose_name_plural = "Blog Views"
        ordering = ["-viewed_at"]



