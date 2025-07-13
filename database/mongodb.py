import asyncio
import time
from typing import Any, Dict, List, Optional

import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import config
from monitoring.metrics import metrics
from utils.logger import logger


class MongoDBSetup:
    """Handles one-time MongoDB setup operations"""
    
    @staticmethod
    def initialize_database():
        """Initialize database, collections, and indexes - call once at startup"""
        try:
            # Create connection for setup
            client = MongoClient(
                config.MONGODB_URI,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True,
                w="majority",
                readPreference="primaryPreferred"
            )
            
            # Test connection
            client.admin.command('ismaster')
            logger.info("Successfully connected to MongoDB Atlas for setup")
            
            db = client[config.MONGODB_DATABASE]
            cache_collection = db[config.MONGODB_COLLECTION]
            
            # Setup collection and indexes
            MongoDBSetup._setup_collection(db, cache_collection)
            
            # Close setup connection
            client.close()
            logger.info("MongoDB setup completed and setup connection closed")
            
        except PyMongoError as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            raise
    
    @staticmethod
    def _setup_collection(db, cache_collection):
        """Setup collection and indexes"""
        try:
            # Create collection if it doesn't exist
            if cache_collection.name not in db.list_collection_names():
                db.create_collection(cache_collection.name)
                logger.info(f"Created collection: {cache_collection.name}")
            
            # Setup indexes
            MongoDBSetup._setup_vector_search_index(cache_collection)
            MongoDBSetup._setup_ttl_indexes(cache_collection)
            
            logger.info("Collection setup completed")
            
        except PyMongoError as e:
            logger.error(f"Failed to setup collection: {e}")
            raise
    
    @staticmethod
    def _setup_vector_search_index(cache_collection):
        """Setup vector search index"""
        try:
            vector_index_definition = {
                "name": config.VECTOR_SEARCH_INDEX_NAME,
                "type": "vectorSearch",
                "definition": {
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding",
                            "numDimensions": config.EMBEDDING_DIMENSIONS,
                            "similarity": "cosine"
                        },
                        {"type": "filter", "path": "user_id"},
                    ]
                }
            }
            
            # Check if vector search index already exists
            try:
                existing_indexes = list(cache_collection.list_search_indexes())
                index_exists = any(idx.get("name") == config.VECTOR_SEARCH_INDEX_NAME for idx in existing_indexes)
                
                if not index_exists:
                    cache_collection.create_search_index(model=vector_index_definition)
                    logger.info(f"Vector search index setup prepared: {config.VECTOR_SEARCH_INDEX_NAME}")
                else:
                    logger.info(f"Vector search index already exists: {config.VECTOR_SEARCH_INDEX_NAME}")
                    
            except Exception as e:
                logger.warning(f"Could not check/create vector search index: {e}")
            
        except PyMongoError as e:
            logger.error(f"Failed to setup vector index: {e}")
    
    @staticmethod
    def _setup_ttl_indexes(cache_collection):
        """Setup TTL indexes for automatic cleanup"""
        try:
            index_info = cache_collection.index_information()
            
            # Main TTL index
            if "timestamp_ttl_idx" not in index_info:
                cache_collection.create_index(
                    [("timestamp", pymongo.ASCENDING)],
                    expireAfterSeconds=config.CACHE_TTL_SECONDS,
                    name="timestamp_ttl_idx"
                )
                logger.info(f"Created TTL index with {config.CACHE_TTL_SECONDS}s expiry")
            else:
                logger.info("TTL index already exists")
                
        except PyMongoError as e:
            logger.error(f"Failed to setup TTL indexes: {e}")


class MongoDBManager:
    """MongoDB Manager"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            # MongoDB connection
            self.client = MongoClient(
                config.MONGODB_URI,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True,
                w="majority",
                readPreference="primaryPreferred"
            )
            
            # Test connection
            self.client.admin.command('ismaster')
            logger.info("Successfully connected to MongoDB Atlas")
            
            # Initialize database and collection references
            self.db = self.client[config.MONGODB_DATABASE]
            self.cache_collection = self.db[config.MONGODB_COLLECTION]
            
            self._initialized = True
            logger.info("MongoDB Manager initialized successfully")
            
        except PyMongoError as e:
            logger.error(f"Failed to initialize MongoDB Manager: {e}")
            raise
    
    def insert_cache_entry(self, entry: Dict[str, Any]) -> bool:
        """Insert a cache entry"""
        try:
            result = self.cache_collection.insert_one(entry)
            success = bool(result.inserted_id)
            
            if success:
                metrics.increment_counter("cache_writes", labels={"status": "success"})
            else:
                metrics.increment_counter("cache_writes", labels={"status": "failed"})
                
            return success
            
        except PyMongoError as e:
            logger.error(f"Failed to insert cache entry: {e}")
            metrics.increment_counter("cache_writes", labels={"status": "error"})
            return False
    
    async def vector_search(
        self,
        user_id: str,
        embedding: List[float],
        threshold: float = config.SIMILARITY_THRESHOLD
    ) -> Optional[Dict[str, Any]]:
        """Perform vector search"""
        
        start_time = time.time()
        
        try:
            # Build filter
            pre_filter = {
                "user_id": {"$eq": user_id}
            }
            
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": config.VECTOR_SEARCH_INDEX_NAME,
                        "path": "embedding",
                        "queryVector": embedding,
                        "numCandidates": config.DEFAULT_NUM_CANDIDATES,
                        "limit": config.MAX_QUERY_LIMIT,
                        "filter": pre_filter
                    }
                },
                {
                    "$addFields": {
                        "vector_score": {"$meta": "vectorSearchScore"}
                    }
                },
                {
                    "$match": {
                        "vector_score": {"$gte": threshold}
                    }
                },
                {
                    "$sort": {
                        "vector_score": -1
                    }
                },
                {
                    "$limit": 1
                }
            ]
            
            results = list(self.cache_collection.aggregate(pipeline))
            search_time = (time.time() - start_time) * 1000
            
            # Record metrics
            metrics.record_histogram("vector_search_latency_ms", search_time)
            
            result = results[0] if results else None
            
            if result:
                logger.info(f"Vector search hit in {search_time:.2f}ms (score: {result.get('vector_score', 'unknown')})")
                metrics.increment_counter("vector_search_total", labels={"result": "hit"})
                return result
            else:
                logger.info(f"Vector search miss in {search_time:.2f}ms")
                metrics.increment_counter("vector_search_total", labels={"result": "miss"})
                return None
                
        except Exception as e:
            search_time = (time.time() - start_time) * 1000
            logger.error(f"Vector search failed in {search_time:.2f}ms: {e}")
            metrics.increment_counter("vector_search_total", labels={"result": "error"})
            return None

def initialize_mongodb():
    """Initialize MongoDB setup - call this once at app startup"""
    MongoDBSetup.initialize_database()


def get_mongodb_manager() -> MongoDBManager:
    """Get MongoDB manager"""
    return MongoDBManager()