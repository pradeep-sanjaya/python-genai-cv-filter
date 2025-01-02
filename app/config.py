import os

# Base paths - use mounted data directory
DATA_DIR = "/data"  # This will be mounted from host
CV_DIR = os.path.join(DATA_DIR, "cv")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CV_DIR, exist_ok=True)

# Weaviate configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

# Schema configuration
SCHEMA_CLASS_NAME = "Resume"
BATCH_SIZE = 100

# File types
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
