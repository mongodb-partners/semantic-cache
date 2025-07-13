import asyncio
from typing import List

import torch
from sentence_transformers import SentenceTransformer

import config
from utils.logger import logger

def get_device():
    """Auto-detect the best available device"""
    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
        print(f"Using NVIDIA GPU: {gpu_name}")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
        print("Using Apple Silicon GPU (MPS)")
    else:
        device = "cpu"
        print("Using CPU")
    return device

class EmbeddingService:
    """Embedding service using all-MiniLM-L6-v2 model"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the all-MiniLM-L6-v2 model"""
        try:
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            # Auto-detect device
            device = get_device()
            print(f"Using device: {device}")
            self._model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
            logger.info(f"Model loaded successfully. Dimension: {self._model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
   
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if not text or not text.strip():
                logger.error("Empty text provided for embedding")
                return []
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                lambda: self._model.encode(text, convert_to_numpy=True).tolist()
            )
            
            logger.debug(f"Generated embedding of dimension {len(embedding)} for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                return []
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._model.encode(valid_texts, convert_to_numpy=True).tolist()
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings for batch of {len(valid_texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return []


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance"""
    return EmbeddingService()