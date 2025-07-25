import os
from typing import Optional
from langchain.chat_models import init_chat_model
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from config.settings import settings

class AIModels:
    def __init__(self):
        self.llm: Optional[any] = None
        self.embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self.vector_store: Optional[InMemoryVectorStore] = None

    def setup_api_key(self, api_key: str):
        os.environ["GOOGLE_API_KEY"] = api_key
        settings.GOOGLE_API_KEY = api_key

    def initialize_models(self) -> bool:
        try:
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API Key không được cung cấp")
            self.llm = init_chat_model(
                model=settings.CHAT_MODEL,
                model_provider=settings.MODEL_PROVIDER
            )
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL
            )
            self.vector_store = InMemoryVectorStore(self.embeddings)
            return True
        except Exception as e:
            print(f"Lỗi khi khởi tạo models: {e}")
            return False

    def is_initialized(self) -> bool:
        return all([
            self.llm is not None,
            self.embeddings is not None,
            self.vector_store is not None
        ])

    def get_llm(self):
        if not self.llm:
            raise ValueError("Chat model chưa được khởi tạo")
        return self.llm

    def get_embeddings(self):
        if not self.embeddings:
            raise ValueError("Embeddings model chưa được khởi tạo")
        return self.embeddings

    def get_vector_store(self):
        if not self.vector_store:
            raise ValueError("Vector store chưa được khởi tạo")
        return self.vector_store

ai_models = AIModels()
