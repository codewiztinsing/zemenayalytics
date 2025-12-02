import os
import pathlib
from environ import Env
from config.logger import logger
# Build paths inside the project
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

# Initialize environ.Env
env = Env(
    DEBUG=(bool, False)
)

# Read .env file if it exists
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    Env.read_env(env_file)


def get_secret(secret_id, backup=None):
    """
    Get secret from environment variables.
    
    Args:
        secret_id: The name of the environment variable to retrieve
        backup: Optional default value if the variable is not found
    
    Returns:
        The value of the environment variable or the backup value
    """
    try:
        # Try to get the value from environment
        value = env(secret_id, default=backup)
        logger.info(f"Secret {secret_id} retrieved: {value}")
        return value
    except Exception as e:
        # If there's an error, return backup or None
        return backup


# Determine which settings to load based on PIPELINE environment variable
PIPELINE = get_secret("PIPELINE", "local")
print("PIPELINE", PIPELINE)

if PIPELINE == "production":
    from .production import *
else:
    from .local import *
  