from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn
from datetime import datetime

import config
from utils.logger import logger
from models.pydantic_models import (
    QueryRequest, CacheEntry, CacheResponse, CacheSaveResponse,
    MetricsResponse
)
from services.cache_service import get_cache_service, CacheService
from database.mongodb import get_mongodb_manager,initialize_mongodb
from monitoring.metrics import get_metrics
from contextlib import asynccontextmanager
from functools import lru_cache


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    try:
        logger.info("Starting semantic cache service...")
        # Initialize MongoDB setup once at startup
        initialize_mongodb()
        logger.info("MongoDB initialization completed")
        get_cache_service()
        logger.info("Semantic cache service started successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    try:
        yield  # Yield control back to FastAPI
    finally:
        # Cleanup on shutdown
        pass


# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION,
    lifespan=lifespan_context
)

# Dependencies
@lru_cache(maxsize=128)
def get_cache_service_dep() -> CacheService:
    """Dependency to get cache service instance"""
    try:
        return get_cache_service()
    except Exception as e:
        logger.error(f"Failed to get cache service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service initialization failed: {str(e)}"
        )

# Health endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": str(datetime.now())}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check"""
    try:
        # Test MongoDB connection
        mongodb = get_mongodb_manager()
        mongodb.client.admin.command('ismaster')
        
        # Test embedding service
        cache_service = get_cache_service()
        test_embedding = await cache_service.embedding_service.generate_embedding("test")
        
        checks = {
            "mongodb": "healthy" if mongodb else "unhealthy",
            "embedding_service": "healthy" if test_embedding else "unhealthy"
        }
        
        all_healthy = all(status == "healthy" for status in checks.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Service info
@app.get("/service-info")
async def get_service_info(cache_service: CacheService = Depends(get_cache_service_dep)):
    """Get current service configuration"""
    return cache_service.get_service_info()

# Metrics endpoint
@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics_endpoint():
    """Get service metrics"""
    return get_metrics()

# Core cache operations
@app.post("/save_to_cache", response_model=CacheSaveResponse)
async def save_to_cache(
    entry: CacheEntry,
    cache_service: CacheService = Depends(get_cache_service_dep)
):
    """Save a query-response entry to the semantic cache"""
    return await cache_service.save_to_cache(entry)


@app.post("/read_cache", response_model=CacheResponse)
async def read_cache(
    request: QueryRequest,
    cache_service: CacheService = Depends(get_cache_service_dep)
):
    """Check if a semantically similar query exists in the cache"""
    return await cache_service.lookup_cache(request)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        reload=config.DEBUG,
        log_level="debug" if config.DEBUG else "info"
    )