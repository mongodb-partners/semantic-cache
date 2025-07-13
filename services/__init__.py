import struct
import numpy as np
from bson import Binary, encode, decode
from enum import Enum
from typing import List
from utils.logger import logger

class VectorType(Enum):
    FLOAT32 = "float32"
    FLOAT16 = "float16" 
    INT8 = "int8"
    BINARY = "binary"

class AtlasBinDataVectorOptimizer:
    """MongoDB Atlas BinData vector optimization with metadata"""
    
    @staticmethod
    def encode_vector_bindata(
        embedding: List[float], 
        vector_type: VectorType = VectorType.INT8
    ) -> Binary:
        """Encode vectors as BinData with metadata for 3x storage savings"""
        
        np_array = np.array(embedding, dtype=np.float32)
        metadata = {
            "vector_type": vector_type.value,
            "dimensions": len(embedding),
            "quantization_version": "v1.0"
        }
        
        if vector_type == VectorType.FLOAT16:
            encoded_data = np_array.astype(np.float16).tobytes()
            binary = encode({"meta": metadata, "data": Binary(encoded_data, subtype=0)})
            
        elif vector_type == VectorType.INT8:
            min_val, max_val = np_array.min(), np_array.max()
            normalized = (np_array - min_val) / (max_val - min_val)
            quantized = (normalized * 255).astype(np.uint8)
            quant_bytes = struct.pack('ff', min_val, max_val) + quantized.tobytes()
            binary = encode({"meta": metadata, "data": Binary(quant_bytes, subtype=1)})
            
        elif vector_type == VectorType.BINARY:
            binary_vector = (np_array > 0).astype(np.uint8)
            packed = np.packbits(binary_vector)
            binary = encode({"meta": metadata, "data": Binary(packed.tobytes(), subtype=2)})
            
        else:  # FLOAT32
            binary = encode({"meta": metadata, "data": Binary(np_array.tobytes(), subtype=0)})
            
        return Binary(binary, subtype=6)  # 6 = BSON-encoded document
    
    @staticmethod
    def decode_vector_bindata(binary_data: Binary) -> List[float]:
        """Decode BinData vectors back to float arrays"""
        
        try:
            parsed = decode(binary_data)
            meta = parsed["meta"]
            data = parsed["data"]
            subtype = data.subtype
            
            if subtype == 0:  # Float data
                if meta["vector_type"] == "float16":
                    return np.frombuffer(data, dtype=np.float16).astype(np.float32).tolist()
                else:
                    return np.frombuffer(data, dtype=np.float32).tolist()
                    
            elif subtype == 1:  # INT8 quantized
                min_val, max_val = struct.unpack('ff', data[:8])
                quantized = np.frombuffer(data[8:], dtype=np.uint8)
                normalized = quantized.astype(np.float32) / 255.0
                restored = normalized * (max_val - min_val) + min_val
                return restored.tolist()
                
            elif subtype == 2:  # Binary quantized
                packed_bits = np.frombuffer(data, dtype=np.uint8)
                binary_vector = np.unpackbits(packed_bits)
                # Convert to float and scale to -1,1
                return (binary_vector.astype(np.float32) * 2 - 1).tolist()
                
            return []
            
        except Exception as e:
            logger.error(f"Failed to decode BinData vector: {e}")
            return []
        