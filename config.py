import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Changed to use current directory
DATA_DIR = os.path.join(BASE_DIR, "data")
CV_DIR = os.path.join(DATA_DIR, "cv")  # Added CV directory path

# Weaviate
WEAVIATE_URL = "http://weaviate:8080"  # Docker service name
WEAVIATE_STARTUP_PERIOD = 30  # Increase startup timeout to 30 seconds

# Create data directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CV_DIR, exist_ok=True)  # Also create CV directory
