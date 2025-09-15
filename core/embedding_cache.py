import os
import json
import pickle
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from langchain_core.documents import Document
    from langchain_core.vectorstores import InMemoryVectorStore
except ImportError:
    # Fallback nếu không có langchain
    Document = None
    InMemoryVectorStore = None

from models.data_models import VietnameseDish

class EmbeddingCache:
    """Cache system for embeddings to reduce API calls"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.embedding_cache_file = os.path.join(cache_dir, "embeddings.pkl")
        self.metadata_cache_file = os.path.join(cache_dir, "metadata.json")
        
        # Tạo cache directory nếu chưa có
        os.makedirs(cache_dir, exist_ok=True)
    
    def _generate_content_hash(self, dishes: List[VietnameseDish]) -> str:
        """Tạo hash từ nội dung các món ăn để detect thay đổi"""
        content_data = []
        for dish in sorted(dishes, key=lambda x: x.name):
            dish_data = {
                'name': dish.name,
                'description': dish.description or '',
                'price': dish.price,
                'category': dish.category or '',
                'region': dish.region or ''
            }
            content_data.append(dish_data)
        
        content_str = json.dumps(content_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def _save_metadata(self, content_hash: str, dish_count: int):
        """Lưu metadata của cache"""
        metadata = {
            'content_hash': content_hash,
            'dish_count': dish_count,
            'cached_at': str(datetime.now()),
            'version': '1.0'
        }
        
        with open(self.metadata_cache_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _load_metadata(self) -> Optional[Dict]:
        """Load metadata của cache"""
        try:
            with open(self.metadata_cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def is_cache_valid(self, dishes: List[VietnameseDish]) -> bool:
        """Kiểm tra xem cache có còn hợp lệ không"""
        if not os.path.exists(self.embedding_cache_file):
            print("🔄 Cache not found - need to create embeddings")
            return False
        
        if not os.path.exists(self.metadata_cache_file):
            print("🔄 Cache metadata not found - need to recreate")
            return False
        
        metadata = self._load_metadata()
        if not metadata:
            print("🔄 Cannot load cache metadata - need to recreate")
            return False
        
        current_hash = self._generate_content_hash(dishes)
        cached_hash = metadata.get('content_hash', '')
        
        if current_hash != cached_hash:
            print("🔄 Dish content changed - need to update embeddings")
            return False
        
        if len(dishes) != metadata.get('dish_count', 0):
            print("🔄 Dish count changed - need to update embeddings")
            return False
        
        print(f"✅ Cache valid - using existing embeddings for {len(dishes)} dishes")
        return True
    
    def save_vector_store(self, vector_store: Any, dishes: List[VietnameseDish]):
        """Lưu vector store vào cache"""
        try:
            print("💾 Saving embeddings to cache...")
            
            # Lưu vector store
            with open(self.embedding_cache_file, 'wb') as f:
                pickle.dump(vector_store, f)
            
            # Lưu metadata
            content_hash = self._generate_content_hash(dishes)
            self._save_metadata(content_hash, len(dishes))
            
            print(f"✅ Cached embeddings for {len(dishes)} dishes")
            
        except Exception as e:
            print(f"❌ Error saving cache: {e}")
    
    def load_vector_store(self) -> Optional[Any]:
        """Load vector store từ cache"""
        try:
            print("📂 Loading embeddings from cache...")
            
            with open(self.embedding_cache_file, 'rb') as f:
                vector_store = pickle.load(f)
            
            print("✅ Successfully loaded cached embeddings")
            return vector_store
            
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
            return None
    
    def clear_cache(self):
        """Xóa cache"""
        try:
            if os.path.exists(self.embedding_cache_file):
                os.remove(self.embedding_cache_file)
            if os.path.exists(self.metadata_cache_file):
                os.remove(self.metadata_cache_file)
            print("🗑️ Cache cleared")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")

# Global cache instance
embedding_cache = EmbeddingCache()