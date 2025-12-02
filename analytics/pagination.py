"""
Custom pagination classes for analytics API.
"""
from rest_framework.pagination import PageNumberPagination
from config.settings import get_secret

# Read pagination settings from environment variables
_PAGE_SIZE = get_secret("API_PAGE_SIZE", backup=100)
_PAGE_SIZE_QUERY_PARAM = get_secret("API_PAGE_SIZE_QUERY_PARAM", backup="page_size")
_MAX_PAGE_SIZE = get_secret("API_MAX_PAGE_SIZE", backup=1000)

# Convert to appropriate types
try:
    _PAGE_SIZE = int(_PAGE_SIZE) if _PAGE_SIZE else 100
except (ValueError, TypeError):
    _PAGE_SIZE = 100

try:
    _MAX_PAGE_SIZE = int(_MAX_PAGE_SIZE) if _MAX_PAGE_SIZE else 1000
except (ValueError, TypeError):
    _MAX_PAGE_SIZE = 1000


class ConfigurablePageNumberPagination(PageNumberPagination):
    """
    Page number pagination with configuration from environment variables.
    
    Configuration via .env:
    - API_PAGE_SIZE: Number of items per page (default: 100)
    - API_PAGE_SIZE_QUERY_PARAM: Query parameter name for page size (default: 'page_size')
    - API_MAX_PAGE_SIZE: Maximum page size allowed (default: 1000)
    
    Usage:
        Add to .env file:
        API_PAGE_SIZE=50
        API_PAGE_SIZE_QUERY_PARAM=page_size
        API_MAX_PAGE_SIZE=500
    """
    page_size = _PAGE_SIZE
    page_size_query_param = _PAGE_SIZE_QUERY_PARAM or "page_size"
    max_page_size = _MAX_PAGE_SIZE
    page_query_param = "page"

