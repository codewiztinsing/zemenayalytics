from django.db import models
from django.contrib.auth.models import User
from analytics.utils.base import BaseModel




class Author(BaseModel):
    """
    Author model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    number_of_blogs = models.IntegerField(default=0)
    number_of_views = models.IntegerField(default=0)
    number_of_likes = models.IntegerField(default=0)
    number_of_comments = models.IntegerField(default=0)
    number_of_shares = models.IntegerField(default=0)
    number_of_reactions = models.IntegerField(default=0)
    number_of_followers = models.IntegerField(default=0)
    number_of_following = models.IntegerField(default=0)


    def __str__(self):
        return f"{self.user.username}"


    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ["-number_of_views"]


    def get_number_of_reactions(self):
        return self.reactions.count()

    def get_number_of_followers(self):
        return self.followers.count()

    def get_number_of_following(self):
        return self.following.count()
