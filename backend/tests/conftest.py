import os
import sys

# Set dummy env vars before any app module is imported so pydantic-settings
# validation doesn't fail in environments without a .env file.
os.environ.setdefault("RAILWAY_TOKEN", "test-token")
os.environ.setdefault("RAILWAY_PROJECT_ID", "test-project")
os.environ.setdefault("RAILWAY_SERVICE_ID", "test-service")
os.environ.setdefault("RAILWAY_WORKSPACE_ID", "test-workspace")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
