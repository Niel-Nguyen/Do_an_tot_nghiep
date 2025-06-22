import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import time
from datetime import datetime

# Import các module tự viết
from config.settings import settings
from models.ai_models import ai_models
from core.chatbot import vietnamese_food_chatbot
from utils.data_loader import data_loader
from models.data_models import ChatMessage

class StreamlitUI:
    """Giao diện Streamlit cho chatbot"""

    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()

    def setup_page_config(self):
        st.set_page_config(
            page_title=settings.APP_TITLE,
            page_icon=settings.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
        # CSS cho giao diện
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            color: #FF6B6B;
            margin-bottom: 2rem;
        }
        .chat-message {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 10px;
            border-left: 4px solid #FF6B6B;
            font-size: 1rem;
        }
        .user-message {
            background-color: #E0F7FA;
            border-left-color: #0288D1;
            color: #01579B;
        }
        .bot-message {
            background-color: #F1F8E9;
            border-left-color: #689F38;
            color: #33691E;
        }
        .stats-card {
            background-color: #FFFFFF;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            margin: 0.5rem 0;
        }
        .suggested-question {
            background-color: #FFF8E1;
            padding: 0.5rem;
            margin: 0.2rem 0;
            border-radius: 5px;
            border-left: 3px solid #FFC107;
            cursor: pointer;
            max-width: 400px;
        }
        </style>
        """, unsafe_allow_html=True)

    def initialize_session_state(self):
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
        if 'api_key_set' not in st.session_state:
            st.session_state.api_key_set = False
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'dishes_loaded' not in st.session_state:
            st.session_state.dishes_loaded = False
        if 'current_stats' not in st.session_state:
            st.session_state.current_stats = {}
        if 'user_input' not in st.session_state:
            st.session_state.user_input = ""

    def render_sidebar(self):
        with st.sidebar:
            st.header("⚙️ Cấu hình")

            if not st.session_state.api_key_set:
                st.subheader("🔑 Google API Key")
                api_key = st.text_input(
                    "Nhập Google API Key:",
                    type="password",
                    help="Cần API key để sử dụng Gemini AI"
                )
                if st.button("Xác nhận API Key"):
                    if api_key:
                        ai_models.setup_api_key(api_key)
                        st.session_state.api_key_set = True
                        st.success("✅ API Key đã được thiết lập!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Vui lòng nhập API Key!")
            else:
                st.success("✅ API Key đã được thiết lập")
                if st.button("🔄 Đổi API Key"):
                    st.session_state.api_key_set = False
                    st.session_state.initialized = False
                    st.experimental_rerun()

            st.divider()

            if st.session_state.initialized:
                st.subheader("📊 Thống kê")
                stats = vietnamese_food_chatbot.get_chatbot_stats()
                st.session_state.current_stats = stats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tổng món ăn", stats['rag_stats']['total_documents'])
                with col2:
                    st.metric("Tin nhắn", stats['conversation_stats']['total_messages'])
                with st.expander("Chi tiết thống kê"):
                    st.json(stats['conversation_stats'])

            st.divider()

            st.subheader("🎛️ Điều khiển")

            if st.button("🗑️ Xóa lịch sử chat"):
                st.session_state.chat_history.clear()
                vietnamese_food_chatbot.clear_conversation()
                st.success("Đã xóa lịch sử chat!")
                st.experimental_rerun()

            if st.button("🔄 Tải lại dữ liệu"):
                self.load_data()
                st.experimental_rerun()

    def load_data(self):
        with st.spinner("Đang tải dữ liệu món ăn..."):
            if data_loader.load_excel_data():
                dishes = data_loader.get_dishes()
                if dishes:
                    if ai_models.initialize_models():
                        if vietnamese_food_chatbot.initialize(dishes):
                            st.session_state.initialized = True
                            st.session_state.dishes_loaded = True
                            st.success(f"✅ Đã tải {len(dishes)} món ăn!")
                            return True
            st.error("❌ Không thể tải dữ liệu món ăn!")
            return False

    def render_main_content(self):
        st.markdown('<div class="main-header">🍜 Chatbot Tư vấn Món Ăn Việt Nam</div>', unsafe_allow_html=True)

        if not st.session_state.api_key_set:
            st.warning("⚠️ Vui lòng nhập Google API Key ở thanh bên để bắt đầu!")
            return

        if not st.session_state.initialized:
            if st.button("🚀 Khởi tạo hệ thống"):
                if self.load_data():
                    st.experimental_rerun()
            return

        self.render_chat_interface()

    def render_chat_interface(self):
        """Render giao diện chat"""
        chat_container = st.container()

        # Hiển thị lịch sử chat
        with chat_container:
            if st.session_state.chat_history:
                for message in st.session_state.chat_history:
                    css_class = "user-message" if message['role'] == 'user' else "bot-message"
                    role_label = "Bạn" if message['role'] == 'user' else "Bot"
                    st.markdown(
                        f'<div class="chat-message {css_class}"><strong>{role_label}:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("👋 Chào bạn! Hãy hỏi tôi về món ăn Việt Nam bạn muốn tìm hiểu!")

        # Gợi ý câu hỏi
        # suggested_questions = [
        #     "🍲 Món nào ngon cho thời tiết nóng?",
        #     "🥗 Gợi ý món ăn ít calo có rau củ?",
        #     "🍤 Có món nào có tôm mà không chiên không?",
        #     "🍚 Tôi muốn món ăn Bắc cho bữa trưa nhẹ"
        # ]

        # st.markdown("### 💡 Gợi ý:")
        # cols = st.columns(2)
        # for idx, question in enumerate(suggested_questions):
        #     if cols[idx % 2].button(question, key=f"suggested_{idx}"):
        #         st.session_state.user_input = question
        #         st.session_state.trigger_submit = True

        # Callback xử lý khi người dùng gửi tin nhắn
        def submit():
            user_input = st.session_state.user_input.strip()
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                response = vietnamese_food_chatbot.chat(user_input)
                st.session_state.chat_history.append({"role": "bot", "content": response})
                st.session_state.user_input = ""
                st.session_state.should_rerun = True

        # Input và xử lý khi nhấn Enter
        st.text_input("Nhập câu hỏi hoặc yêu cầu của bạn:", key="user_input", on_change=submit)

        # Xử lý gửi từ gợi ý (gán cờ trigger_submit=True)
        if st.session_state.get("trigger_submit", False):
            submit()
            st.session_state.trigger_submit = False

        # Rerun nếu cần
        if st.session_state.get("should_rerun", False):
            st.session_state.should_rerun = False
            st.rerun()



if __name__ == "__main__":
    ui = StreamlitUI()
    ui.render_sidebar()
    ui.render_main_content()
