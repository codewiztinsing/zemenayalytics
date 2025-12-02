"""
Swagger/OpenAPI utilities for analytics views.

Provides mixins and helpers for consistent API documentation.
"""
from typing import List, Dict, Any, Optional
from drf_spectacular.utils import extend_schema, OpenApiParameter


class SwaggerMixin:
    """
    Mixin class to provide Swagger/OpenAPI schema decorators for analytics views.
    
    Usage:
        class MyView(SwaggerMixin, APIView):
            swagger_operation_id = "my_operation"
            swagger_summary = "My operation summary"
            swagger_description = "Detailed description"
            swagger_request_serializer = MyRequestSerializer
            swagger_response_serializer = MyResponseSerializer
            
            def get_swagger_parameters(self):
                return self.get_common_parameters() + [
                    OpenApiParameter(...)  # Add view-specific parameters
                ]
            
            @self.get_swagger_schema()
            def get(self, request):
                ...
    """
    
    # Override these in subclasses
    swagger_operation_id: str = ""
    swagger_summary: str = ""
    swagger_description: str = ""
    swagger_request_serializer = None
    swagger_response_serializer = None
    swagger_tags: List[str] = ["Analytics"]
    
    def get_common_parameters(self) -> List[OpenApiParameter]:
        """
        Get common parameters used across all analytics endpoints.
        
        Returns:
            List of OpenApiParameter for date range and pagination
        """
        return [
            OpenApiParameter(
                name="start",
                description="The start date of the analytics (ISO format: YYYY-MM-DD)",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="end",
                description="The end date of the analytics (ISO format: YYYY-MM-DD)",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="page",
                description="The page number of the analytics",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="page_size",
                description="The page size of the analytics",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
        ]
    
    def get_swagger_parameters(self) -> List[OpenApiParameter]:
        """
        Get all Swagger parameters for this view.
        Override this method in subclasses to add view-specific parameters.
        
        Returns:
            List of OpenApiParameter including common and view-specific parameters
        """
        return self.get_common_parameters()
    
    def get_swagger_responses(self) -> Dict[int, Any]:
        """
        Get Swagger response definitions.
        Override this method in subclasses to customize responses.
        
        Returns:
            Dictionary mapping status codes to response schemas
        """
        responses = {
            200: self.swagger_response_serializer(many=True) if self.swagger_response_serializer else None,
            400: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"}
                }
            }
        }
        return {k: v for k, v in responses.items() if v is not None}
    
    def get_swagger_schema_decorator(self):
        """
        Get the extend_schema decorator for this view instance.
        This can be used directly as a decorator.
        
        Usage in view:
            @extend_schema(...)  # Use the output of this method
            def get(self, request):
                ...
        """
        return extend_schema(
            operation_id=self.swagger_operation_id,
            summary=self.swagger_summary,
            description=self.swagger_description,
            tags=self.swagger_tags,
            request=self.swagger_request_serializer,
            parameters=self.get_swagger_parameters(),
            responses=self.get_swagger_responses(),
        )


# Helper functions for common parameter patterns

def create_enum_parameter(
    name: str,
    description: str,
    enum_values: List[str],
    required: bool = False,
    default: Optional[str] = None,
) -> OpenApiParameter:
    """
    Create an OpenApiParameter for an enum field.
    
    Args:
        name: Parameter name
        description: Parameter description
        enum_values: List of allowed enum values
        required: Whether the parameter is required
        default: Default value (optional)
    
    Returns:
        OpenApiParameter configured for enum
    """
    return OpenApiParameter(
        name=name,
        description=description,
        required=required,
        type=str,
        enum=enum_values,
        location=OpenApiParameter.QUERY,
    )


def create_integer_parameter(
    name: str,
    description: str,
    required: bool = False,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> OpenApiParameter:
    """
    Create an OpenApiParameter for an integer field.
    
    Args:
        name: Parameter name
        description: Parameter description
        required: Whether the parameter is required
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
    
    Returns:
        OpenApiParameter configured for integer
    """
    param = OpenApiParameter(
        name=name,
        description=description,
        required=required,
        type=int,
        location=OpenApiParameter.QUERY,
    )
    # Note: min/max validation would be handled by serializer
    return param


def create_string_parameter(
    name: str,
    description: str,
    required: bool = False,
) -> OpenApiParameter:
    """
    Create an OpenApiParameter for a string field.
    
    Args:
        name: Parameter name
        description: Parameter description
        required: Whether the parameter is required
    
    Returns:
        OpenApiParameter configured for string
    """
    return OpenApiParameter(
        name=name,
        description=description,
        required=required,
        type=str,
        location=OpenApiParameter.QUERY,
    )


# Pre-defined parameter sets for common use cases

def get_date_range_parameters() -> List[OpenApiParameter]:
    """Get date range parameters (start, end)."""
    return [
        create_string_parameter(
            name="start",
            description="The start date of the analytics (ISO format: YYYY-MM-DD)",
            required=False,
        ),
        create_string_parameter(
            name="end",
            description="The end date of the analytics (ISO format: YYYY-MM-DD)",
            required=False,
        ),
    ]


def get_pagination_parameters() -> List[OpenApiParameter]:
    """Get pagination parameters (page, page_size)."""
    return [
        create_integer_parameter(
            name="page",
            description="The page number of the analytics",
            required=False,
        ),
        create_integer_parameter(
            name="page_size",
            description="The page size of the analytics",
            required=False,
        ),
    ]


def get_time_range_parameters() -> List[OpenApiParameter]:
    """Get time range enum parameters (month, week, day, year)."""
    return [
        create_enum_parameter(
            name="range",
            description="Time range for aggregation",
            enum_values=["month", "week", "year", "day"],
            required=False,
        ),
    ]


def get_compare_parameters() -> List[OpenApiParameter]:
    """Get comparison period parameters (month, week, day, year)."""
    return [
        create_enum_parameter(
            name="compare",
            description="Period size for comparison",
            enum_values=["month", "week", "day", "year"],
            required=False,
            default="month",
        ),
    ]

