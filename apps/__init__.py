"""
Compat package to provide legacy import paths like ``apps.analytics``.

The project has been migrated to use the top-level ``analytics`` app, but
some external integrations (e.g. existing Celery Beat schedules) still
reference the old ``apps.analytics.*`` dotted paths.

Keeping this lightweight package avoids import errors without changing
the new app layout.
"""


