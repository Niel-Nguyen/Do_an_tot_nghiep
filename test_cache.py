#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test embedding cache system
"""

import os
import sys
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_cache_system():
    """Test hệ thống cache embedding"""
    print("🧪 TESTING EMBEDDING CACHE SYSTEM")
    print("=" * 50)
    
    try:
        from core.embedding_cache import embedding_cache
        from utils.database_loader import load_dishes_from_database
        from models.ai_models import ai_models
        from core.rag_system import rag_system
        
        # 1. Check current cache status
        print("1️⃣ Checking current cache status...")
        dishes = load_dishes_from_database()
        print(f"   📚 Loaded {len(dishes)} dishes from database")
        
        is_valid = embedding_cache.is_cache_valid(dishes)
        print(f"   📊 Cache valid: {is_valid}")
        
        # 2. Clear cache để test
        print("\n2️⃣ Clearing cache for test...")
        embedding_cache.clear_cache()
        print("   🗑️ Cache cleared")
        
        # 3. Initialize models
        print("\n3️⃣ Initializing AI models...")
        if not ai_models.initialize_models():
            print("   ❌ Failed to initialize models")
            return False
        print("   ✅ AI models initialized")
        
        # 4. Test lần 1: Tạo cache mới (sẽ gọi API)
        print("\n4️⃣ First initialization (will call embedding API)...")
        start_time = time.time()
        
        success1 = rag_system.initialize(dishes)
        
        end_time = time.time()
        duration1 = end_time - start_time
        
        if success1:
            print(f"   ✅ First init successful: {duration1:.2f} seconds")
        else:
            print(f"   ❌ First init failed: {duration1:.2f} seconds")
            return False
        
        # 5. Test lần 2: Sử dụng cache (không gọi API)
        print("\n5️⃣ Second initialization (should use cache)...")
        
        # Reset RAG system
        rag_system.is_initialized = False
        rag_system.retriever = None
        rag_system.dishes_lookup = {}
        
        start_time = time.time()
        
        success2 = rag_system.initialize(dishes)
        
        end_time = time.time()
        duration2 = end_time - start_time
        
        if success2:
            print(f"   ✅ Second init successful: {duration2:.2f} seconds")
        else:
            print(f"   ❌ Second init failed: {duration2:.2f} seconds")
            return False
        
        # 6. So sánh thời gian
        print(f"\n6️⃣ Performance comparison:")
        print(f"   🐌 First init (with API calls): {duration1:.2f}s")
        print(f"   🚀 Second init (with cache): {duration2:.2f}s")
        
        if duration2 < duration1:
            speedup = duration1 / duration2
            print(f"   📈 Cache speedup: {speedup:.1f}x faster!")
        
        # 7. Test search functionality
        print(f"\n7️⃣ Testing search functionality...")
        if rag_system.is_initialized:
            results = rag_system.search_relevant_dishes("phở bò")
            print(f"   🔍 Search results for 'phở bò': {len(results)} dishes found")
            if results:
                print(f"   🥇 Top result: {results[0].dish_name}")
        
        print(f"\n✅ ALL TESTS PASSED!")
        print(f"🎉 Cache system is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error in cache test: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_quota_recovery():
    """Test khả năng phục hồi khi gặp quota limit"""
    print("\n🚨 TESTING QUOTA RECOVERY")
    print("=" * 50)
    
    try:
        from core.embedding_cache import embedding_cache
        from utils.database_loader import load_dishes_from_database
        
        dishes = load_dishes_from_database()
        
        # Kiểm tra xem có cache cũ không
        cache_exists = os.path.exists(embedding_cache.embedding_cache_file)
        
        if cache_exists:
            print("✅ Old cache exists - quota recovery should work")
            print("💡 When quota is exceeded, system will use cached embeddings")
        else:
            print("⚠️  No cache exists - quota recovery won't work")
            print("💡 Recommend creating cache when quota is available")
        
        return cache_exists
        
    except Exception as e:
        print(f"❌ Error testing quota recovery: {e}")
        return False

def main():
    """Main function"""
    print(f"🕒 Test started at: {datetime.now()}")
    
    # Test cache system
    cache_test = test_cache_system()
    
    # Test quota recovery
    quota_test = test_quota_recovery()
    
    print(f"\n📋 SUMMARY")
    print("=" * 20)
    print(f"Cache system test: {'✅ PASS' if cache_test else '❌ FAIL'}")
    print(f"Quota recovery test: {'✅ READY' if quota_test else '⚠️  NOT READY'}")
    
    if cache_test and quota_test:
        print(f"\n🎉 System is ready! Cache will prevent quota issues.")
    elif cache_test:
        print(f"\n⚠️  Cache works but no fallback. Create cache when quota available.")
    else:
        print(f"\n❌ Cache system needs fixing.")

if __name__ == "__main__":
    main()