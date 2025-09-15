#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script quản lý embedding cache
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def show_cache_status():
    """Hiển thị trạng thái cache"""
    print("📊 EMBEDDING CACHE STATUS")
    print("=" * 50)
    
    try:
        from core.embedding_cache import embedding_cache
        from utils.database_loader import load_dishes_from_database
        
        cache_dir = embedding_cache.cache_dir
        embedding_file = embedding_cache.embedding_cache_file
        metadata_file = embedding_cache.metadata_cache_file
        
        print(f"📁 Cache directory: {cache_dir}")
        print(f"📄 Embedding file: {embedding_file}")
        print(f"📄 Metadata file: {metadata_file}")
        
        # Check file existence và size
        if os.path.exists(embedding_file):
            size = os.path.getsize(embedding_file) / (1024*1024)  # MB
            mtime = datetime.fromtimestamp(os.path.getmtime(embedding_file))
            print(f"✅ Embedding cache exists: {size:.2f} MB (modified: {mtime})")
        else:
            print("❌ Embedding cache not found")
        
        if os.path.exists(metadata_file):
            mtime = datetime.fromtimestamp(os.path.getmtime(metadata_file))
            print(f"✅ Metadata cache exists (modified: {mtime})")
            
            # Load và hiển thị metadata
            metadata = embedding_cache._load_metadata()
            if metadata:
                print(f"   📋 Cached dishes: {metadata.get('dish_count', 0)}")
                print(f"   📅 Cached at: {metadata.get('cached_at', 'Unknown')}")
                print(f"   🔢 Content hash: {metadata.get('content_hash', 'Unknown')[:16]}...")
        else:
            print("❌ Metadata cache not found")
        
        # Check current dishes
        print(f"\n🍜 Current dishes status:")
        dishes = load_dishes_from_database()
        print(f"   📊 Current dishes: {len(dishes)}")
        
        # Check cache validity
        is_valid = embedding_cache.is_cache_valid(dishes)
        if is_valid:
            print("   ✅ Cache is valid and can be used")
        else:
            print("   ⚠️  Cache is invalid or needs update")
            
    except Exception as e:
        print(f"❌ Error checking cache status: {e}")

def clear_cache():
    """Xóa cache"""
    print("🗑️  CLEARING EMBEDDING CACHE")
    print("=" * 50)
    
    try:
        from core.embedding_cache import embedding_cache
        embedding_cache.clear_cache()
        print("✅ Cache cleared successfully")
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def force_rebuild_cache():
    """Force rebuild cache"""
    print("🔄 FORCE REBUILDING EMBEDDING CACHE")
    print("=" * 50)
    
    try:
        # Clear old cache
        from core.embedding_cache import embedding_cache
        embedding_cache.clear_cache()
        
        # Initialize models
        from models.ai_models import ai_models
        from config.settings import settings
        
        if not ai_models.initialize_models():
            print("❌ Failed to initialize AI models")
            return
        
        # Load dishes
        from utils.database_loader import load_dishes_from_database
        dishes = load_dishes_from_database()
        print(f"📚 Loaded {len(dishes)} dishes")
        
        # Initialize RAG (will create new cache)
        from core.rag_system import rag_system
        success = rag_system.initialize(dishes)
        
        if success:
            print("✅ Cache rebuilt successfully!")
        else:
            print("❌ Failed to rebuild cache")
            
    except Exception as e:
        print(f"❌ Error rebuilding cache: {e}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_cache.py status    - Show cache status")
        print("  python manage_cache.py clear     - Clear cache")
        print("  python manage_cache.py rebuild   - Force rebuild cache")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_cache_status()
    elif command == "clear":
        clear_cache()
    elif command == "rebuild":
        force_rebuild_cache()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, clear, rebuild")

if __name__ == "__main__":
    main()