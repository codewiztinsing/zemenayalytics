"""
Management command to populate database with test data using Factory Boy.

Usage:
    python manage.py populate_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.analytics.models import Country, Blog, BlogView
from apps.analytics.factories import CountryFactory, BlogFactory, BlogViewFactory
from config.settings import get_secret


class Command(BaseCommand):
    help = "Populate database with test data using Factory Boy"

    def add_arguments(self, parser):
        parser.add_argument(
            "--countries",
            type=int,
            help="Number of countries to create (overrides env var)",
        )
        parser.add_argument(
            "--blogs",
            type=int,
            help="Number of blogs to create (overrides env var)",
        )
        parser.add_argument(
            "--blog-views",
            type=int,
            help="Number of blog views to create (overrides env var)",
        )
        parser.add_argument(
            "--users",
            type=int,
            help="Number of users to create (overrides env var)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before populating",
        )

    def handle(self, *args, **options):
        # Get counts from environment variables or command arguments
        countries_count = options.get("countries") or int(get_secret("FACTORY_COUNTRIES", backup=10))
        blogs_count = options.get("blogs") or int(get_secret("FACTORY_BLOGS", backup=50))
        blog_views_count = options.get("blog_views") or int(get_secret("FACTORY_BLOG_VIEWS", backup=500))
        users_count = options.get("users") or int(get_secret("FACTORY_USERS", backup=5))

        if options.get("clear"):
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            BlogView.objects.all().delete()
            Blog.objects.all().delete()
            Country.objects.all().delete()
            # Don't delete superuser
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        # Create users if needed (at least 1 user is required for blogs)
        existing_users = User.objects.count()
        min_users = max(1, users_count)  # Ensure at least 1 user
        if existing_users < min_users:
            users_to_create = min_users - existing_users
            self.stdout.write(f"Creating {users_to_create} users...")
            for i in range(users_to_create):
                User.objects.create_user(
                    username=f"user{i+1}",
                    email=f"user{i+1}@example.com",
                    password="testpass123",
                    first_name=f"User{i+1}",
                    last_name="Test"
                )
            self.stdout.write(self.style.SUCCESS(f"Created {users_to_create} users."))
        else:
            self.stdout.write(f"Using existing {existing_users} users.")

        # Create countries (at least 1 country is recommended)
        existing_countries = Country.objects.count()
        if existing_countries < countries_count:
            countries_to_create = countries_count - existing_countries
            self.stdout.write(f"Creating {countries_to_create} countries...")
            CountryFactory.create_batch(countries_to_create)
            self.stdout.write(self.style.SUCCESS(f"Created {countries_to_create} countries."))
        else:
            self.stdout.write(f"Using existing {existing_countries} countries.")

        # Ensure we have at least one country for blogs
        if Country.objects.count() == 0:
            self.stdout.write(self.style.WARNING("No countries found. Creating 1 default country..."))
            CountryFactory.create()
            self.stdout.write(self.style.SUCCESS("Default country created."))

        # Create blogs (requires users)
        if User.objects.count() == 0:
            self.stdout.write(self.style.ERROR("No users found. Cannot create blogs. Please create users first."))
            return

        existing_blogs = Blog.objects.count()
        if existing_blogs < blogs_count:
            blogs_to_create = blogs_count - existing_blogs
            self.stdout.write(f"Creating {blogs_to_create} blogs...")
            BlogFactory.create_batch(blogs_to_create)
            self.stdout.write(self.style.SUCCESS(f"Created {blogs_to_create} blogs."))
        else:
            self.stdout.write(f"Using existing {existing_blogs} blogs.")

        # Create blog views (requires blogs)
        if Blog.objects.count() == 0:
            self.stdout.write(self.style.WARNING("No blogs found. Skipping blog views creation."))
        else:
            existing_views = BlogView.objects.count()
            if existing_views < blog_views_count:
                views_to_create = blog_views_count - existing_views
                self.stdout.write(f"Creating {views_to_create} blog views...")
                # Create in batches to avoid memory issues
                batch_size = 100
                for i in range(0, views_to_create, batch_size):
                    batch = min(batch_size, views_to_create - i)
                    BlogViewFactory.create_batch(batch)
                    if (i + batch) % 500 == 0:
                        self.stdout.write(f"  Created {i + batch} views...")
                self.stdout.write(self.style.SUCCESS(f"Created {views_to_create} blog views."))
            else:
                self.stdout.write(f"Using existing {existing_views} blog views.")

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("Data population complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Countries: {Country.objects.count()}")
        self.stdout.write(f"Blogs: {Blog.objects.count()}")
        self.stdout.write(f"Blog Views: {BlogView.objects.count()}")

