"""
Post-processing hooks for drf-spectacular to customize OpenAPI schema.
"""


def remove_schemas_from_components(result, generator, request, public):
    """
    Remove schemas from components section in OpenAPI schema.
    This hook removes the 'schemas' key from the 'components' section.
    """
    if "components" in result and "schemas" in result["components"]:
        del result["components"]["schemas"]
    return result

