"""
Compat package for the legacy ``apps.analytics`` module path.

New code should import from the top-level ``analytics`` app instead,
but this module exists to keep older references (e.g. Celery beat task
paths) working without modification.
"""


