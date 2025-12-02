"""
Management command to populate database with test data using Factory Boy.

Usage:
    python manage.py populate_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analytics.models import Country, Blog, BlogView, Author
from analytics.factories import CountryFactory, BlogFactory, BlogViewFactory
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
        # Default to 100 records for all tables
        # Use 'is not None' to properly handle 0 as a valid value
        countries_count = options.get("countries") if options.get("countries") is not None else int(get_secret("FACTORY_COUNTRIES", backup=100))
        blogs_count = options.get("blogs") if options.get("blogs") is not None else int(get_secret("FACTORY_BLOGS", backup=100))
        blog_views_count = options.get("blog_views") if options.get("blog_views") is not None else int(get_secret("FACTORY_BLOG_VIEWS", backup=100))
        users_count = options.get("users") if options.get("users") is not None else int(get_secret("FACTORY_USERS", backup=100))

        if options.get("clear"):
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            BlogView.objects.all().delete()
            Blog.objects.all().delete()
            Country.objects.all().delete()
            # Don't delete superuser
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        # Create users if needed (default: 100 users)
        existing_users = User.objects.count()
        # Only create users if users_count > 0
        if users_count > 0 and existing_users < users_count:
            users_to_create = users_count - existing_users
            self.stdout.write(f"Creating {users_to_create} users...")
            created_count = 0
            for i in range(users_to_create):
                # Use get_or_create to avoid duplicate username errors
                user, created = User.objects.get_or_create(
                    username=f"user{i+1}",
                    defaults={
                        'email': f"user{i+1}@example.com",
                        'first_name': f"User{i+1}",
                        'last_name': "Test"
                    }
                )
                if created:
                    user.set_password("testpass123")
                    user.save()
                    created_count += 1
                
                # Ensure Author exists for this user
                Author.objects.get_or_create(user=user)
            
            self.stdout.write(self.style.SUCCESS(f"Created {created_count} new users (skipped {users_to_create - created_count} existing)."))
        else:
            self.stdout.write(f"Using existing {existing_users} users.")
        
        # Ensure all users have corresponding Author objects
        users_without_authors = User.objects.filter(author__isnull=True)
        if users_without_authors.exists():
            self.stdout.write(f"Creating Author objects for {users_without_authors.count()} users without authors...")
            for user in users_without_authors:
                Author.objects.get_or_create(user=user)
            self.stdout.write(self.style.SUCCESS("Author objects created."))

        # Create countries
        existing_countries = Country.objects.count()
        if countries_count > 0 and existing_countries < countries_count:
            countries_to_create = countries_count - existing_countries
            self.stdout.write(f"Creating {countries_to_create} countries...")
            created_count = 0
            attempts = 0
            max_attempts = countries_to_create * 10  # Prevent infinite loop
            
            while created_count < countries_to_create and attempts < max_attempts:
                try:
                    country = CountryFactory.build()
                    country, was_created = Country.objects.get_or_create(
                        code=country.code,
                        defaults={
                            'name': country.name,
                            'continent': country.continent
                        }
                    )
                    if was_created:
                        created_count += 1
                except Exception:
                    # If there's a duplicate or other error, try again with a new factory instance
                    pass
                attempts += 1
            
            if created_count < countries_to_create:
                self.stdout.write(self.style.WARNING(
                    f"Created {created_count} countries (attempted {countries_to_create}, "
                    f"may have hit duplicate codes or names)."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(f"Created {created_count} countries."))
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
        if blogs_count > 0 and existing_blogs < blogs_count:
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
            if blog_views_count > 0 and existing_views < blog_views_count:
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

