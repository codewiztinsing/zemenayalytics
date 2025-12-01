from django.contrib import admin
from .models import Blog, BlogView, Country, Author, BlogViewTimeSeriesAggregate, BlogCreationTimeSeriesAggregate


class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")
    list_filter = ("code",)
    search_fields = ("code", "name")
    ordering = ("name",)


class BlogAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "country", "created_at")
    list_filter = ("created_at", "country")
    search_fields = ("title", "author__username", "author__email", "country__name")
    ordering = ("-created_at",)
    raw_id_fields = ("author", "country")


class BlogViewAdmin(admin.ModelAdmin):
    list_display = ("id", "blog", "user", "viewed_at")
    list_filter = ("viewed_at",)
    search_fields = ("blog__title", "user__username", "user__email")
    ordering = ("-viewed_at",)
    raw_id_fields = ("blog", "user")



class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "bio", "number_of_blogs", "number_of_views", "number_of_likes", "number_of_comments", "number_of_shares", "number_of_reactions", "number_of_followers", "number_of_following")
    list_filter = ("number_of_blogs", "number_of_views", "number_of_likes", "number_of_comments", "number_of_shares", "number_of_reactions", "number_of_followers", "number_of_following")
    search_fields = ("user__username", "user__email")
    ordering = ("-number_of_views",)
    raw_id_fields = ("user",)



class BlogViewTimeSeriesAggregateAdmin(admin.ModelAdmin):
    list_display = ("id", "granularity", "time_bucket", "blog", "country", "author", "view_count", "unique_blogs_viewed", "unique_users")
    list_filter = ("granularity", "time_bucket", "blog", "country", "author")
    search_fields = ("blog__title", "country__name", "author__user__username", "author__user__email")
    ordering = ("-time_bucket",)
    raw_id_fields = ("blog", "country", "author")

class BlogCreationTimeSeriesAggregateAdmin(admin.ModelAdmin):
    list_display = ("id", "granularity", "time_bucket", "country", "author", "blog_count")
    list_filter = ("granularity", "time_bucket", "country", "author")
    search_fields = ("country__name", "author__user__username", "author__user__email")
    ordering = ("-time_bucket",)
    raw_id_fields = ("country", "author")

admin.site.register(BlogViewTimeSeriesAggregate, BlogViewTimeSeriesAggregateAdmin)
admin.site.register(BlogCreationTimeSeriesAggregate, BlogCreationTimeSeriesAggregateAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogView, BlogViewAdmin)
admin.site.register(Author, AuthorAdmin)