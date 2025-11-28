from django.db import models
from django.contrib.auth.models import User


class Country(models.Model):
    """
    Simple Country model used in examples.
    """
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    def get_code_and_name(self):
        return f"{self.code} - {self.name}"





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


class BlogView(models.Model):
    """
    Each record represents a view of a blog.
    We aggregate counts of these rows to compute 'views'.
    """
    blog = models.ForeignKey(Blog, related_name="views", on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Viewed {self.blog.title} by {self.user.get_full_name()}"

    def get_viewed_at_date(self):
        return self.viewed_at.date()

    def get_viewed_at_time(self):
        return self.viewed_at.time()

    def get_viewed_at_datetime(self):
        return self.viewed_at