from .base import *
from config.settings import get_secret
from config.logger import logger

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Optional in-memory database (useful for tests)
USE_IN_MEMORY_DB = str(get_secret("USE_IN_MEMORY_DB", "false")).lower() in {"1", "true", "yes"}

if USE_IN_MEMORY_DB:
    logger.info("Using in-memory SQLite database (USE_IN_MEMORY_DB is enabled)")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    # Use PostgreSQL if environment variables are set (for Docker), otherwise use SQLite file
    DB_NAME = get_secret("DB_NAME")
    DB_USER = get_secret("DB_USER")
    DB_PASSWORD = get_secret("DB_PASSWORD")
    DB_HOST = get_secret("DB_HOST", "db")  # Default to 'db' for docker-compose service name
    DB_PORT = get_secret("DB_PORT", "5432")

    logger.info(f"DB_NAME: {DB_NAME}")
    logger.info(f"DB_USER: {DB_USER}")
    logger.info(f"DB_PASSWORD: {DB_PASSWORD}")
    logger.info(f"DB_HOST: {DB_HOST}")
    logger.info(f"DB_PORT: {DB_PORT}")

    if DB_NAME and DB_USER and DB_PASSWORD:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": DB_NAME,
                "USER": DB_USER,
                "PASSWORD": DB_PASSWORD,
                "HOST": DB_HOST,
                "PORT": DB_PORT,
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

