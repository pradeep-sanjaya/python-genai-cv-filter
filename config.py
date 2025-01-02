import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Weaviate
WEAVIATE_URL = "http://weaviate:8080"  # Docker service name
WEAVIATE_STARTUP_PERIOD = 30  # Increase startup timeout to 30 seconds

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)
