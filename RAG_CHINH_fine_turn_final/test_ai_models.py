import sys
sys.path.append('.')

from models.ai_models import ai_models

print("=== Testing AI Models ===")
print(f"AI Models initialized: {ai_models.is_initialized()}")

try:
    print("Initializing AI models...")
    ai_models.initialize_models()
    print(f"After init - AI Models initialized: {ai_models.is_initialized()}")
    
    if ai_models.is_initialized():
        print("✅ AI Models ready")
        
        # Test vector store
        vector_store = ai_models.get_vector_store()
        print(f"Vector store: {type(vector_store)}")
        
        # Test LLM
        llm = ai_models.get_llm()
        print(f"LLM: {type(llm)}")
        
    else:
        print("❌ AI Models failed to initialize")
        
except Exception as e:
    print(f"❌ Error initializing AI models: {e}")
    import traceback
    traceback.print_exc()
