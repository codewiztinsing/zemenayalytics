"""
Unit tests for analytics views.
"""
import json
from urllib.parse import quote
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.analytics.models import Country, Blog, BlogView, Author
from datetime import datetime, timedelta
from django.utils import timezone


class BlogViewsAnalyticsViewTest(TestCase):
    """Test cases for BlogViewsAnalyticsView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Create Author for this user
        self.author = Author.objects.create(user=self.user)
        self.country = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )
        self.blog = Blog.objects.create(
            title="Test Blog",
            author=self.author,
            country=self.country
        )
        # Create some views
        for _ in range(3):
            BlogView.objects.create(blog=self.blog, user=self.user)

    def test_blog_views_analytics_by_country(self):
        """Test blog views analytics endpoint with country grouping."""
        url = "/api/v1/analytics/blog-views/?object_type=country"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

    def test_blog_views_analytics_by_user(self):
        """Test blog views analytics endpoint with user grouping."""
        url = "/api/v1/analytics/blog-views/?object_type=user"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_blog_views_analytics_with_filters(self):
        """Test blog views analytics endpoint with filters."""
        filters = json.dumps({
            "eq": {
                "field": "blog.country.code",
                "value": "US"
            }
        })
        url = f"/api/v1/analytics/blog-views/?object_type=country&filters={quote(filters)}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blog_views_analytics_with_date_range(self):
        """Test blog views analytics endpoint with date range."""
        start = (timezone.now() - timedelta(days=30)).date().isoformat()
        end = timezone.now().date().isoformat()
        url = f"/api/v1/analytics/blog-views/?object_type=country&start={start}&end={end}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blog_views_analytics_invalid_data(self):
        """Test blog views analytics endpoint with invalid data."""
        url = "/api/v1/analytics/blog-views/?object_type=invalid_type"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blog_views_analytics_invalid_filter_format(self):
        """Test blog views analytics endpoint with invalid filter format."""
        # Test with Swagger's additionalProp pattern (invalid)
        filters = json.dumps({
            "additionalProp1": "string",
            "additionalProp2": "string"
        })
        url = f"/api/v1/analytics/blog-views/?object_type=country&filters={quote(filters)}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("filter", response.data.get("filters", [""])[0].lower() if isinstance(response.data.get("filters"), list) else str(response.data).lower())

    def test_blog_views_analytics_empty_result(self):
        """Test blog views analytics with no data."""
        # Delete all views
        BlogView.objects.all().delete()
        
        url = "/api/v1/analytics/blog-views/?object_type=country"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


class TopAnalyticsViewTest(TestCase):
    """Test cases for TopAnalyticsView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Create Author for this user
        self.author = Author.objects.create(user=self.user)
        self.country = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )
        self.blog = Blog.objects.create(
            title="Popular Blog",
            author=self.author,
            country=self.country
        )
        # Create multiple views
        for _ in range(5):
            BlogView.objects.create(blog=self.blog, user=self.user)

    def test_top_analytics_blogs(self):
        """Test top analytics endpoint for blogs."""
        url = "/api/v1/analytics/top/?top=blog"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

    def test_top_analytics_users(self):
        """Test top analytics endpoint for users."""
        url = "/api/v1/analytics/top/?top=user"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_top_analytics_countries(self):
        """Test top analytics endpoint for countries."""
        url = "/api/v1/analytics/top/?top=country"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_top_analytics_with_filters(self):
        """Test top analytics endpoint with filters."""
        filters = json.dumps({
            "eq": {
                "field": "blog.country.code",
                "value": "US"
            }
        })
        url = f"/api/v1/analytics/top/?top=blog&filters={quote(filters)}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_top_analytics_invalid_type(self):
        """Test top analytics endpoint with invalid type."""
        url = "/api/v1/analytics/top/?top=invalid"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_top_analytics_pagination(self):
        """Test that top analytics response is paginated."""
        url = "/api/v1/analytics/top/?top=blog"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)


class PerformanceAnalyticsViewTest(TestCase):
    """Test cases for PerformanceAnalyticsView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Create Author for this user
        self.author = Author.objects.create(user=self.user)
        self.country = Country.objects.create(
            code="US",
            name="United States",
            continent="North America"
        )
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

    def test_performance_analytics_month(self):
        """Test performance analytics endpoint with month comparison."""
        url = "/api/v1/analytics/performance/?compare=month"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

    def test_performance_analytics_week(self):
        """Test performance analytics endpoint with week comparison."""
        url = "/api/v1/analytics/performance/?compare=week"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_analytics_day(self):
        """Test performance analytics endpoint with day comparison."""
        url = "/api/v1/analytics/performance/?compare=day"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_analytics_year(self):
        """Test performance analytics endpoint with year comparison."""
        url = "/api/v1/analytics/performance/?compare=year"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_analytics_with_user_id(self):
        """Test performance analytics endpoint with user filter."""
        url = f"/api/v1/analytics/performance/?compare=month&user_id={self.user.id}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_analytics_with_filters(self):
        """Test performance analytics endpoint with filters."""
        filters = json.dumps({
            "eq": {
                "field": "blog.country.code",
                "value": "US"
            }
        })
        url = f"/api/v1/analytics/performance/?compare=month&filters={quote(filters)}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_analytics_invalid_compare(self):
        """Test performance analytics endpoint with invalid compare value."""
        url = "/api/v1/analytics/performance/?compare=invalid"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check that there's an error in the response (could be "detail" or field-level error)
        self.assertTrue("detail" in response.data or "compare" in response.data)

    def test_performance_analytics_pagination(self):
        """Test that performance analytics response is paginated."""
        url = "/api/v1/analytics/performance/?compare=day"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

