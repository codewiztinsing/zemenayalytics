from django.contrib import admin
from .models import Blog, BlogView, Country


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


admin.site.register(Country, CountryAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(BlogView, BlogViewAdmin)