import os
from environ import Env

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        return value
    except Exception as e:
        # If there's an error, return backup or None
        return backup


# Determine which settings to load based on PIPELINE environment variable
PIPELINE = get_secret("PIPELINE", "local")

if PIPELINE == "production":
    from .production import *
else:
    from .local import *
  