import time
from typing import Any, Dict

import config
from database.mongodb import get_mongodb_manager
from models.pydantic_models import CacheEntry, QueryRequest
from monitoring.metrics import log_vector_search_metrics, metrics
from services.embedding_service import get_embedding_service
from utils.logger import logger


class CacheService:
    """semantic cache service"""
    
    def __init__(self):
        self.mongodb = get_mongodb_manager()
        self.embedding_service = get_embedding_service()
    
    async def save_to_cache(self, entry: CacheEntry) -> Dict[str, Any]:
        """Save entry to cache"""
        start_time = time.time()
        
        try:
            # Generate embedding if not provided
            if not entry.embedding:
                entry.embedding = await self.embedding_service.generate_embedding(entry.query)
            
            if not entry.embedding:
                return {
                    "message": "Failed to save to cache",
                    "error": "Embedding generation failed"
                }
            
            # Prepare entry
            entry_dict = entry.to_dict()
            
            # Add additional fields
            entry_dict.update({
                "embedding": entry.embedding
            })
            
            success = self.mongodb.insert_cache_entry(entry_dict)
            save_time = (time.time() - start_time) * 1000
            
            if success:
                metrics.record_histogram("cache_save_latency_ms", save_time)
                logger.info(f"Saved to cache in {save_time:.2f}ms (user: {entry.user_id})")
                return {"message": "Successfully saved to cache"}
            else:
                return {
                    "message": "Failed to save to cache", 
                    "error": "Database insert failed"
                }
                
        except Exception as e:
            save_time = (time.time() - start_time) * 1000
            logger.error(f"Cache save failed in {save_time:.2f}ms: {e}")
            return {
                "message": "Failed to save to cache",
                "error": str(e)
            }
    
    async def lookup_cache(self, request: QueryRequest) -> Dict[str, Any]:
        """Look up cache entry"""
        start_time = time.time()
        
        try:
            # Use provided threshold or default
            threshold = request.threshold if request.threshold is not None else config.SIMILARITY_THRESHOLD
            
            # Generate embedding
            embedding = await self.embedding_service.generate_embedding(request.query)
            if not embedding:
                return {
                    "response": "",
                    "error": "Embedding generation failed"
                }
            
            # Perform vector search
            result = await self.mongodb.vector_search(
                user_id=request.user_id,
                embedding=embedding,
                threshold=threshold
            )
            
            total_time = (time.time() - start_time) * 1000
            
            if result:
                # Log metrics
                await log_vector_search_metrics(
                    user_id=request.user_id,
                    latency_ms=total_time,
                    num_candidates=config.DEFAULT_NUM_CANDIDATES,
                    result_score=result.get("vector_score", 0),
                    cache_hit=True
                )
                
                return {
                    "response": result["response"],
                    "latency_ms": total_time,
                    "similarity_score": result.get("vector_score", 0)
                }
            
            # Log cache miss
            await log_vector_search_metrics(
                user_id=request.user_id,
                latency_ms=total_time,
                num_candidates=config.DEFAULT_NUM_CANDIDATES,
                result_score=0,
                cache_hit=False
            )
            
            return {
                "response": "cache_miss",
                "latency_ms": total_time
            }
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            logger.error(f"Cache lookup failed in {total_time:.2f}ms: {e}")
            return {
                "response": "",
                "error": str(e),
                "latency_ms": total_time
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            "embedding_model": config.EMBEDDING_MODEL,
            "embedding_dimensions": config.EMBEDDING_DIMENSIONS,
            "default_similarity_threshold": config.SIMILARITY_THRESHOLD
        }

def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return CacheService()