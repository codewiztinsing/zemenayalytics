"""
Unit tests for analytics services.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from analytics.models import Country, Blog, BlogView, Author
from analytics.services.blog_services import BlogViewsAnalyticsService
from analytics.services.top_service import TopAnalyticsService
from analytics.services.performance_service import PerformanceAnalyticsService
from datetime import datetime, timedelta
from django.utils import timezone


class BlogViewsAnalyticsServiceTest(TestCase):
    """Test cases for BlogViewsAnalyticsService."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123"
        )
        self.country1 = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )
        self.country2 = Country.objects.create(
            code="ET",
            name="Ethiopia",
            continent="Africa"
        )
        # Create authors for users
        self.author1 = Author.objects.create(user=self.user1)
        self.author2 = Author.objects.create(user=self.user2)
        self.blog1 = Blog.objects.create(
            title="Blog 1",
            author=self.author1,
            country=self.country1
        )
        self.blog2 = Blog.objects.create(
            title="Blog 2",
            author=self.author2,
            country=self.country2
        )
        # Create blog views
        BlogView.objects.create(blog=self.blog1, user=self.user1)
        BlogView.objects.create(blog=self.blog1, user=self.user2)
        BlogView.objects.create(blog=self.blog2, user=self.user1)

    def test_get_analytics_with_filters(self):
        """Test getting analytics with filters."""
        filters = {
            "eq": {
                "field": "blog.country.code",
                "value": "US"
            }
        }
        result = BlogViewsAnalyticsService.get_analytics("country", filters=filters)
        
        self.assertIsInstance(result, list)
        # Should only return US country
        if result:
            self.assertIn("United States", result[0]["x"])

    def test_get_analytics_with_date_range(self):
        """Test getting analytics with date range."""
        start = (timezone.now() - timedelta(days=30)).date().isoformat()
        end = timezone.now().date().isoformat()
        
        result = BlogViewsAnalyticsService.get_analytics(
            "country",
            start=start,
            end=end
        )
        
        self.assertIsInstance(result, list)


class TopAnalyticsServiceTest(TestCase):
    """Test cases for TopAnalyticsService."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123"
        )
        self.country = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )
        # Create authors for users
        self.author1 = Author.objects.create(user=self.user1)
        self.author2 = Author.objects.create(user=self.user2)
        self.blog1 = Blog.objects.create(
            title="Popular Blog",
            author=self.author1,
            country=self.country
        )
        self.blog2 = Blog.objects.create(
            title="Another Blog",
            author=self.author2,
            country=self.country
        )
        # Create multiple views for blog1
        for _ in range(5):
            BlogView.objects.create(blog=self.blog1, user=self.user1)
        # Create fewer views for blog2
        for _ in range(2):
            BlogView.objects.create(blog=self.blog2, user=self.user2)

    def test_get_top_analytics_blog(self):
        """Test get_top_analytics with blog type."""
        result = TopAnalyticsService.get_top_analytics("blog", limit=10)
        
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 10)

    def test_get_top_analytics_user(self):
        """Test get_top_analytics with user type."""
        result = TopAnalyticsService.get_top_analytics("user", limit=10)
        
        self.assertIsInstance(result, list)

    def test_get_top_analytics_country(self):
        """Test get_top_analytics with country type."""
        result = TopAnalyticsService.get_top_analytics("country", limit=10)
        
        self.assertIsInstance(result, list)


class PerformanceAnalyticsServiceTest(TestCase):
    """Test cases for PerformanceAnalyticsService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.country = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )
        # Create author for user
        self.author = Author.objects.create(user=self.user)
        self.blog = Blog.objects.create(
            title="Test Blog",
            author=self.author,
            country=self.country
        )
        # Create views at different times
        now = timezone.now()
        for i in range(5):
            BlogView.objects.create(
                blog=self.blog,
                user=self.user,
                viewed_at=now - timedelta(days=i)
            )

    def test_get_performance_analytics_month(self):
        """Test getting performance analytics by month."""
        result = PerformanceAnalyticsService.get_performance_analytics("month")
        
        self.assertIsInstance(result, list)
        
        # Check structure
        for item in result:
            self.assertIn("x", item)
            self.assertIn("y", item)
            self.assertIn("z", item)
            self.assertIsInstance(item["y"], int)

    def test_get_performance_analytics_week(self):
        """Test getting performance analytics by week."""
        result = PerformanceAnalyticsService.get_performance_analytics("week")
        
        self.assertIsInstance(result, list)

    def test_get_performance_analytics_day(self):
        """Test getting performance analytics by day."""
        result = PerformanceAnalyticsService.get_performance_analytics("day")
        
        self.assertIsInstance(result, list)

    def test_get_performance_analytics_year(self):
        """Test getting performance analytics by year."""
        result = PerformanceAnalyticsService.get_performance_analytics("year")
        
        self.assertIsInstance(result, list)

    def test_get_performance_analytics_invalid_compare(self):
        """Test that invalid compare value raises ValueError."""
        with self.assertRaises(ValueError):
            PerformanceAnalyticsService.get_performance_analytics("invalid")

    def test_get_performance_analytics_with_user_id(self):
        """Test getting performance analytics filtered by user."""
        result = PerformanceAnalyticsService.get_performance_analytics(
            "month",
            user_id=self.user.id
        )
        
        self.assertIsInstance(result, list)

    def test_get_performance_analytics_with_filters(self):
        """Test getting performance analytics with filters."""
        filters = {
            "eq": {
                "field": "blog.country.code",
                "value": "US"
            }
        }
        result = PerformanceAnalyticsService.get_performance_analytics(
            "month",
            filters=filters
        )
        
        self.assertIsInstance(result, list)

