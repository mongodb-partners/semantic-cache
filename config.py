import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Application settings
APP_NAME = "MongoDB-Semantic-Cache"
APP_VERSION = "2.0"
APP_DESCRIPTION = "MongoDB Atlas Semantic Cache"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Service configuration
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8183"))

# MongoDB Atlas configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "semantic_cache")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "cache")
VECTOR_SEARCH_INDEX_NAME = os.getenv("VECTOR_SEARCH_INDEX_NAME", "cache_vector_index")

# Cache configuration
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))

# Embedding configuration (all-MiniLM-L6-v2)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384  # all-MiniLM-L6-v2 output dimension

DEFAULT_NUM_CANDIDATES = int(os.getenv("DEFAULT_NUM_CANDIDATES", "1000"))
MAX_QUERY_LIMIT = int(os.getenv("MAX_QUERY_LIMIT", "10"))

# Monitoring
LOG_VECTOR_METRICS = True
