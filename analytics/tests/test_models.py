"""
Unit tests for analytics models.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from analytics.models import Country, Blog, BlogView, Author
from datetime import datetime


class CountryModelTest(TestCase):
    """Test cases for Country model."""

    def setUp(self):
        """Set up test data."""
        self.country = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )

    def test_country_creation(self):
        """Test country creation."""
        self.assertEqual(self.country.code, "US")
        self.assertEqual(self.country.name, "United States")
        self.assertEqual(self.country.continent, "North America")

    def test_country_str(self):
        """Test country string representation."""
        self.assertEqual(str(self.country), "United States")

    def test_get_code_and_name(self):
        """Test get_code_and_name method."""
        result = self.country.get_code_and_name()
        self.assertEqual(result, "US - United States")

    def test_country_unique_code(self):
        """Test that country code must be unique."""
        with self.assertRaises(Exception):
            Country.objects.create(
                code="US",
                name="Another US",
                continent="North America"
            )


class BlogModelTest(TestCase):
    """Test cases for Blog model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        # Blog.author now points to Author, so create corresponding Author
        self.author = Author.objects.create(user=self.user)
        self.country = Country.objects.create(
            code="ET",
            name="Ethiopia",
            continent="Africa"
        )
        self.blog = Blog.objects.create(
            title="Test Blog Post",
            author=self.author,
            country=self.country
        )

    def test_blog_creation(self):
        """Test blog creation."""
        self.assertEqual(self.blog.title, "Test Blog Post")
        # Blog.author is an Author instance linked to the user
        self.assertEqual(self.blog.author, self.author)
        self.assertEqual(self.blog.author.user, self.user)
        self.assertEqual(self.blog.country, self.country)
        self.assertIsNotNone(self.blog.created_at)

    def test_blog_str(self):
        """Test blog string representation."""
        self.assertEqual(str(self.blog), "Test Blog Post")

    def test_get_author_name(self):
        """Test get_author_name method."""
        result = self.blog.get_author_name()
        self.assertEqual(result, "Test User")

    def test_blog_without_country(self):
        """Test blog can be created without country."""
        blog = Blog.objects.create(
            title="Blog Without Country",
            author=self.author,
            country=None
        )
        self.assertIsNone(blog.country)

    def test_blog_cascade_delete(self):
        """Test that blog is deleted when user is deleted."""
        blog_id = self.blog.id
        self.user.delete()
        self.assertFalse(Blog.objects.filter(id=blog_id).exists())

    def test_blog_set_null_on_country_delete(self):
        """Test that blog country is set to null when country is deleted."""
        country_id = self.country.id
        self.country.delete()
        self.blog.refresh_from_db()
        self.assertIsNone(self.blog.country)


class BlogViewModelTest(TestCase):
    """Test cases for BlogView model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="testpass123"
        )
        author_user = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="testpass123"
        )
        # Create Author instance for the blog author
        self.author = Author.objects.create(user=author_user)
        self.country = Country.objects.create(
            code="KE",
            name="Kenya",
            continent="Africa"
        )
        self.blog = Blog.objects.create(
            title="Popular Blog",
            author=self.author,
            country=self.country
        )
        self.blog_view = BlogView.objects.create(
            blog=self.blog,
            user=self.user
        )

    def test_blog_view_creation(self):
        """Test blog view creation."""
        self.assertEqual(self.blog_view.blog, self.blog)
        self.assertEqual(self.blog_view.user, self.user)
        self.assertIsNotNone(self.blog_view.viewed_at)

    def test_blog_view_str_with_user(self):
        """Test blog view string representation with user."""
        expected = f"Viewed {self.blog.title} by {self.user.get_full_name()}"
        self.assertEqual(str(self.blog_view), expected)

    def test_blog_view_str_without_user(self):
        """Test blog view string representation without user."""
        anonymous_view = BlogView.objects.create(
            blog=self.blog,
            user=None
        )
        expected = f"Viewed {self.blog.title} by anonymous"
        self.assertEqual(str(anonymous_view), expected)

    def test_get_viewed_at_date(self):
        """Test get_viewed_at_date method."""
        date = self.blog_view.get_viewed_at_date()
        self.assertEqual(date, self.blog_view.viewed_at.date())

    def test_get_viewed_at_time(self):
        """Test get_viewed_at_time method."""
        time = self.blog_view.get_viewed_at_time()
        self.assertEqual(time, self.blog_view.viewed_at.time())

    def test_get_viewed_at_datetime(self):
        """Test get_viewed_at_datetime method."""
        datetime_obj = self.blog_view.get_viewed_at_datetime()
        self.assertEqual(datetime_obj, self.blog_view.viewed_at)

    def test_blog_view_cascade_delete(self):
        """Test that blog view is deleted when blog is deleted."""
        view_id = self.blog_view.id
        self.blog.delete()
        self.assertFalse(BlogView.objects.filter(id=view_id).exists())

    def test_blog_view_set_null_on_user_delete(self):
        """Test that blog view user is set to null when user is deleted."""
        user_id = self.user.id
        self.user.delete()
        self.blog_view.refresh_from_db()
        self.assertIsNone(self.blog_view.user)

