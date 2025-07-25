import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Google API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # Model Configuration
    CHAT_MODEL = "gemini-2.0-flash"
    EMBEDDING_MODEL = "models/embedding-001"
    MODEL_PROVIDER = "google_genai"
    
    # App Configuration
    APP_TITLE = os.getenv("APP_TITLE", "🍜 Chatbot Tư vấn Món Ăn Việt Nam")
    APP_ICON = os.getenv("APP_ICON", "🍜")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Data Configuration
    DATA_FILE_PATH = "data\mon_an_viet_nam.xlsx"
    
    # RAG Configuration
    SIMILARITY_SEARCH_K = 3
    MAX_DOCS_FOR_CONTEXT = 5
    
    # UI Configuration
    SIDEBAR_WIDTH = 300
    CHAT_INPUT_PLACEHOLDER = "Hỏi tôi về món ăn Việt Nam..."

settings = Settings()