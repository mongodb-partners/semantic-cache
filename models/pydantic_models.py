from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Model for cache lookup requests"""
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="The query text to look up")
    threshold: Optional[float] = Field(None, description="Optional similarity threshold (0.0 to 1.0)", ge=0.0, le=1.0)

class CacheEntry(BaseModel):
    """Model for cache entries"""
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="The query text")
    response: str = Field(..., description="The cached response")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the cache entry")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the query")

    def to_dict(self) -> dict:
        """Convert model to dictionary for MongoDB storage"""
        result = self.dict(exclude_none=True)
        
        # Ensure timestamp is set
        if self.timestamp is None:
            result["timestamp"] = datetime.now(timezone.utc)
            
        return result

class CacheResponse(BaseModel):
    """Model for cache lookup responses"""
    response: str = Field(..., description="The cached response or cache_miss if not found")
    latency_ms: Optional[float] = Field(None, description="Query latency in milliseconds")
    similarity_score: Optional[float] = Field(None, description="Vector similarity score")
    error: Optional[str] = Field(None, description="Error message if applicable")

class CacheSaveResponse(BaseModel):
    """Model for cache save responses"""
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if applicable")

class MetricsResponse(BaseModel):
    """Model for metrics response"""
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    counters: dict = Field(..., description="Counter metrics")
    gauges: dict = Field(..., description="Gauge metrics") 
    histograms: dict = Field(..., description="Histogram metrics with percentiles")