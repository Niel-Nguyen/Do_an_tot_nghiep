import os
from typing import Optional
from langchain.chat_models import init_chat_model
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from config.settings import settings

class AIModels:
    """Quản lý các AI models"""
    
    def __init__(self):
        self.llm: Optional[any] = None
        self.embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self.vector_store: Optional[InMemoryVectorStore] = None
        
    def setup_api_key(self, api_key: str):
        """Thiết lập Google API Key"""
        os.environ["GOOGLE_API_KEY"] = api_key
        settings.GOOGLE_API_KEY = api_key
    
    def initialize_models(self) -> bool:
        """Khởi tạo tất cả các models"""
        try:
            # Kiểm tra API key
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API Key không được cung cấp")
            
            # 1. Khởi tạo Chat Model - Gemini 2.0 Flash
            self.llm = init_chat_model(
                model=settings.CHAT_MODEL,
                model_provider=settings.MODEL_PROVIDER
            )
            
            # 2. Khởi tạo Embeddings Model
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL
            )
            
            # 3. Khởi tạo Vector Store
            self.vector_store = InMemoryVectorStore(self.embeddings)
            
            return True
            
        except Exception as e:
            print(f"Lỗi khi khởi tạo models: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Kiểm tra xem các models đã được khởi tạo chưa"""
        return all([
            self.llm is not None,
            self.embeddings is not None,
            self.vector_store is not None
        ])
    
    def get_llm(self):
        """Lấy chat model"""
        if not self.llm:
            raise ValueError("Chat model chưa được khởi tạo")
        return self.llm
    
    def get_embeddings(self):
        """Lấy embeddings model"""
        if not self.embeddings:
            raise ValueError("Embeddings model chưa được khởi tạo")
        return self.embeddings
    
    def get_vector_store(self):
        """Lấy vector store"""
        if not self.vector_store:
            raise ValueError("Vector store chưa được khởi tạo")
        return self.vector_store

# Global instance
ai_models = AIModels()