"""
Post-processing hooks for drf-spectacular to customize OpenAPI schema.
"""


def remove_schemas_from_components(result, generator, request, public):
    """
    Remove request schemas from components section, but keep pagination and response schemas.
    This hook removes request schemas but preserves pagination and response schemas that are still referenced.
    """
    if "components" in result and "schemas" in result["components"]:
        schemas = result["components"]["schemas"]
        # Keep pagination schemas and response schemas (remove request schemas)
        kept_schemas = {}
        for key, value in schemas.items():
            # Keep pagination schemas
            if key.startswith("Paginated") and key.endswith("List"):
                kept_schemas[key] = value
            # Keep response schemas (but not request schemas)
            elif key.endswith("Response") and not key.endswith("Request"):
                kept_schemas[key] = value
        # Update schemas to only include kept schemas
        result["components"]["schemas"] = kept_schemas
    return result


def remove_api_prefixes_from_paths(result, generator, request, public):
    """
    Remove /api/, /api/v1/, and /v1/ prefixes from all paths in the OpenAPI schema.
    This makes the Swagger UI show cleaner paths without version prefixes.
    
    Note: SCHEMA_PATH_PREFIX="/api/" strips /api/ first, so paths may already
    be /analytics/... or /v1/analytics/... when this hook runs.
    """
    if "paths" in result:
        new_paths = {}
        for path, path_item in result["paths"].items():
            new_path = path
            # Remove /api/v1/ prefix first (longer match)
            if new_path.startswith("/api/v1/"):
                new_path = new_path.replace("/api/v1/", "/", 1)
            # Remove /api/ prefix
            elif new_path.startswith("/api/"):
                new_path = new_path.replace("/api/", "/", 1)
            # Remove /v1/ prefix (in case SCHEMA_PATH_PREFIX already stripped /api/)
            elif new_path.startswith("/v1/"):
                new_path = new_path.replace("/v1/", "/", 1)
            new_paths[new_path] = path_item
        result["paths"] = new_paths
    return result

