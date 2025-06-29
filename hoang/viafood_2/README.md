🍜 Vietnamese Food Chatbot - Cấu trúc Project
📁 Cấu trúc thư mục:
vietnamese_food_chatbot/
│
├── requirements.txt          # Các thư viện cần thiết
├── .env.                     # File cấu hình
├── README.md                 # Hướng dẫn sử dụng
│
├── config/
│   └── settings.py           # Cấu hình hệ thống
│
├── models/
│   ├── __init__.py
│   ├── ai_models.py          # Khởi tạo các AI models
│   └── data_models.py        # Định nghĩa cấu trúc dữ liệu
│
├── utils/
│   ├── __init__.py
│   ├── data_loader.py        # Đọc và xử lý file món ăn
│   └── text_processor.py     # Xử lý văn bản
│
├── core/
│   ├── __init__.py
│   ├── chatbot.py           # Logic chính của chatbot
│   └── rag_system.py        # Hệ thống RAG
│
├── ui/
│   ├── __init__.py
│   └── streamlit_app.py     # Giao diện Streamlit
│
├── data/
│   └── mon_an_viet_nam.xlsx  # File dữ liệu món ăn của bạn
│
└── main.py                  # File chạy chính


Cách chạy:

Cài đặt: pip install -r requirements.txt

"
Tạo file .env
# Google API Key for Gemini
GOOGLE_API_KEY=?????

# App Configuration
APP_TITLE=Vietnamese Food Chatbot
APP_ICON=🍜
DEBUG=False
"

Đặt file món ăn vào thư mục data/(xlsx)
Chạy: streamlit run main.py

Mô tả từng component:

config/: Cấu hình hệ thống và API keys
models/: Khởi tạo AI models và định nghĩa data structures
utils/: Các tiện ích xử lý dữ liệu
core/: Logic nghiệp vụ chính
ui/: Giao diện người dùng
data/: Dữ liệu món ăn

nếu build được mà lỗi thì 
pip install --upgrade langchain
pip install --upgrade langchain-google-genai
pip install --upgrade google-generativeai
pip install --upgrade packaging
pip install --upgrade google-cloud-bigquery