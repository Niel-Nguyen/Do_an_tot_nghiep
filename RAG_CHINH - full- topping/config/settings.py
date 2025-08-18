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
    DATA_FILE_PATH = "data100mon.xlsx"
    
    # RAG Configuration
    SIMILARITY_SEARCH_K = 20  # Tăng từ 10 lên 20 để có nhiều món hơn
    MAX_DOCS_FOR_CONTEXT = 25  # Tăng từ 12 lên 25 để có nhiều context hơn
    
    # UI Configuration
    SIDEBAR_WIDTH = 300
    CHAT_INPUT_PLACEHOLDER = "Hỏi tôi về món ăn Việt Nam..."

settings = Settings()
