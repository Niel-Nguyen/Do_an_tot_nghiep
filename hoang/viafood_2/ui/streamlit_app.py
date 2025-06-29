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
from utils.audio_handler import audio_handler, StreamlitAudioComponents


class StreamlitUI:
    """Giao diện Streamlit cho chatbot với tính năng audio"""

    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()

    # ---------------------------------------------------------------------
    # 1️⃣  Thiết lập giao diện và trạng thái
    # ---------------------------------------------------------------------
    def setup_page_config(self):
        st.set_page_config(
            page_title=settings.APP_TITLE,
            page_icon=settings.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # CSS tuỳ chỉnh
        st.markdown(
            """
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
        .audio-controls {
            background-color: #F8F9FA;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border: 1px solid #DEE2E6;
        }
        .microphone-status {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .mic-available {
            background-color: #D4EDDA;
            color: #155724;
        }
        .mic-unavailable {
            background-color: #F8D7DA;
            color: #721C24;
        }
        .recording-indicator {
            animation: pulse 1.5s ease-in-out infinite;
            color: #DC3545;
        }
        .microphone-float-button {
            position: absolute;
            top: 20px;
            right: 30px;
            background-color: #FF6B6B;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 24px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            cursor: pointer;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    # Thêm nút ghi âm nổi trên góc phải trong thanh chat
    def render_floating_microphone(self):
        st.markdown(
            """
            <button class="microphone-float-button" onclick="window.location.reload();">
                🎤
            </button>
            """,
            unsafe_allow_html=True,
        )
        if st.session_state.audio_enabled and not st.session_state.is_recording:
            self.handle_voice_input()


    def initialize_session_state(self):
        """Khởi tạo tất cả biến session_state cần thiết chỉ 1 lần"""
        default_states = {
            "initialized": False,
            "api_key_set": False,
            "chat_history": [],
            "dishes_loaded": False,
            "current_stats": {},
            "user_input": "",
            # 🔊 Audio states
            "audio_enabled": True,
            "auto_play_response": False,
            "recording_duration": 5,
            "is_recording": False,
        }
        for k, v in default_states.items():
            st.session_state.setdefault(k, v)

    # ---------------------------------------------------------------------
    # 2️⃣  SIDEBAR cấu hình, thống kê & điều khiển
    # ---------------------------------------------------------------------
    def render_sidebar(self):
        with st.sidebar:
            st.header("⚙️ Cấu hình")

            # 2.1 API Key
            if not st.session_state.api_key_set:
                st.subheader("🔑 Google API Key")
                api_key = st.text_input(
                    "Nhập Google API Key:",
                    type="password",
                    help="Cần API key để sử dụng Gemini AI",
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

            # 2.2 Audio settings
            st.subheader("🎵 Cài đặt âm thanh")

            mic_available = audio_handler.is_microphone_available()
            mic_status_class = "mic-available" if mic_available else "mic-unavailable"
            mic_status_text = "🟢 Có sẵn" if mic_available else "🔴 Không có"
            st.markdown(
                f'<span class="microphone-status {mic_status_class}">Microphone: {mic_status_text}</span>',
                unsafe_allow_html=True,
            )

            st.session_state.audio_enabled = st.checkbox(
                "🔊 Bật tính năng âm thanh",
                value=st.session_state.audio_enabled,
                help="Bật/tắt Text‑to‑Speech và Speech‑to‑Text",
            )

            if st.session_state.audio_enabled:
                st.session_state.auto_play_response = st.checkbox(
                    "🎤 Tự động phát âm phản hồi",
                    value=st.session_state.auto_play_response,
                    help="Phát âm thanh khi bot trả lời",
                )
                st.session_state.recording_duration = st.slider(
                    "⏱️ Thời gian ghi âm (giây)",
                    min_value=3,
                    max_value=15,
                    value=st.session_state.recording_duration,
                )

            st.divider()

            # 2.3 Thống kê
            if st.session_state.initialized:
                st.subheader("📊 Thống kê")
                stats = vietnamese_food_chatbot.get_chatbot_stats()
                st.session_state.current_stats = stats

                col1, col2 = st.columns(2)
                col1.metric("Tổng món ăn", stats["rag_stats"]["total_documents"])
                col2.metric("Tin nhắn", stats["conversation_stats"]["total_messages"])

                with st.expander("Chi tiết thống kê"):
                    st.json(stats["conversation_stats"])

            st.divider()

            # 2.4 Điều khiển nhanh
            st.subheader("🎛️ Điều khiển")

            if st.button("🗑️ Xóa lịch sử chat"):
                st.session_state.chat_history.clear()
                vietnamese_food_chatbot.clear_conversation()
                st.success("Đã xóa lịch sử chat!")
                st.experimental_rerun()

            if st.button("🔄 Tải lại dữ liệu"):
                self.load_data()
                st.experimental_rerun()

    # ---------------------------------------------------------------------
    # 3️⃣  Khởi tạo và nạp dữ liệu RAG
    # ---------------------------------------------------------------------
    def load_data(self) -> bool:
        with st.spinner("Đang tải dữ liệu món ăn..."):
            if data_loader.load_excel_data():
                dishes = data_loader.get_dishes()
                if dishes and ai_models.initialize_models() and vietnamese_food_chatbot.initialize(dishes):
                    st.session_state.initialized = True
                    st.session_state.dishes_loaded = True
                    st.success(f"✅ Đã tải {len(dishes)} món ăn!")
                    return True
        st.error("❌ Không thể tải dữ liệu món ăn!")
        return False

    # ---------------------------------------------------------------------
    # 4️⃣  Main Content (Header → Init Button → Chat)
    # ---------------------------------------------------------------------
    def render_main_content(self):
        st.markdown(
            '<div class="main-header">🍜 Chatbot Tư vấn Món Ăn Việt Nam</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.api_key_set:
            st.warning("⚠️ Vui lòng nhập Google API Key ở thanh bên để bắt đầu!")
            return

        if not st.session_state.initialized:
            if st.button("🚀 Khởi tạo hệ thống"):
                if self.load_data():
                    st.experimental_rerun()
            return

        # Khi đã sẵn sàng → hiển thị Chat UI
        self.render_chat_interface()

    # ---------------------------------------------------------------------
    # 5️⃣  Chat Interface (Audio + History + Input)
    # ---------------------------------------------------------------------
    def render_chat_interface(self):
        # 5.1 Audio controls (ghi âm câu hỏi)
        if st.session_state.audio_enabled:
            self.render_audio_controls()

        # 5.2 Khung chat
        chat_container = st.container()
        with chat_container:
            if st.session_state.chat_history:
                for i, msg in enumerate(st.session_state.chat_history):
                    css_class = "user-message" if msg["role"] == "user" else "bot-message"
                    role_label = "Bạn" if msg["role"] == "user" else "Bot 🤖"

                    if msg["role"] == "user":
                        st.markdown(
                            f'<div class="chat-message {css_class}"><strong>{role_label}:</strong> {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        col1, col2 = st.columns([1, 15])
                        with col1:
                            if st.session_state.audio_enabled and st.button("🔊", key=f"tts_{i}"):
                                audio_bytes = audio_handler.text_to_speech(msg["content"], play_audio=False)
                                if audio_bytes:
                                    player = audio_handler.create_audio_player_html(audio_bytes)
                                    st.markdown(player, unsafe_allow_html=True)
                        with col2:
                            st.markdown(
                                f'<div class="chat-message {css_class}"><strong>{role_label}:</strong> {msg["content"]}</div>',
                                unsafe_allow_html=True,
                            )
            else:
                st.info("👋 Chào bạn! Hãy hỏi tôi về món ăn Việt Nam bạn muốn tìm hiểu!")

        # 5.3 Input (text & voice)
        self.render_input_section()

    # ---------------------------------------------------------------------
    # 5.3.1 Audio ghi âm
    # ---------------------------------------------------------------------
    def render_audio_controls(self):
        st.markdown('<div class="audio-controls">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 2, 3])

        with col1:
            if st.button("🎤", disabled=st.session_state.is_recording):
                self.handle_voice_input()

        with col2:
            if st.session_state.is_recording:
                st.markdown('<div class="recording-indicator">🔴 Đang ghi âm...</div>', unsafe_allow_html=True)

        with col3:
            if audio_handler.is_microphone_available():
                st.success("✅ Microphone sẵn sàng")
            else:
                st.error("❌ Không tìm thấy microphone")

        st.markdown('</div>', unsafe_allow_html=True)

    def render_input_section(self):
        """Render input section với cả text và voice"""
        st.subheader("💬 Nhập câu hỏi")
        
        # Text input
        def submit_text():
            user_input = st.session_state.user_input.strip()
            if user_input:
                self.process_user_input(user_input)

        st.text_input(
            "Nhập câu hỏi hoặc yêu cầu của bạn:",
            key="user_input",
            on_change=submit_text,
            placeholder="VD: Gợi ý món ăn miền Bắc cho bữa tối..."
        )
        
        # Gợi ý câu hỏi
        # if st.expander("💡 Gợi ý câu hỏi", expanded=False):
        #     suggested_questions = [
        #         "🍲 Món nào ngon cho thời tiết nóng?",
        #         "🥗 Gợi ý món ăn chay có rau củ?",
        #         "🍤 Có món nào có tôm mà không chiên không?",
        #         "🍚 Tôi muốn món ăn Bắc cho bữa trưa nhẹ",
        #         "🍜 Cách làm phở bò truyền thống?",
        #         "🥮 Nguyên liệu làm bánh chưng là gì?"
        #     ]
            
        #     cols = st.columns(2)
        #     for idx, question in enumerate(suggested_questions):
        #         if cols[idx % 2].button(question.replace("🍲 ", "").replace("🥗 ", "").replace("🍤 ", "").replace("🍚 ", "").replace("🍜 ", "").replace("🥮 ", ""), 
        #                                key=f"suggest_{idx}"):
        #             self.process_user_input(question)

    def handle_voice_input(self):
        """Xử lý voice input"""
        if not audio_handler.is_microphone_available():
            st.error("❌ Microphone không khả dụng!")
            return
        
        try:
            st.session_state.is_recording = True
            
            with st.spinner(f"🎤 Đang ghi âm trong {st.session_state.recording_duration} giây..."):
                # Ghi âm và nhận dạng
                recognized_text = audio_handler.speech_to_text(
                    duration=st.session_state.recording_duration
                )
            
            st.session_state.is_recording = False
            
            if recognized_text:
                st.success(f"✅ Đã nhận dạng: '{recognized_text}'")
                self.process_user_input(recognized_text)
            else:
                st.warning("⚠️ Không thể nhận dạng giọng nói. Vui lòng thử lại!")
                
        except Exception as e:
            st.session_state.is_recording = False
            st.error(f"❌ Lỗi khi ghi âm: {str(e)}")

    def process_user_input(self, user_input: str):
        """Xử lý input từ người dùng"""
        # Thêm tin nhắn người dùng
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Tạo phản hồi từ bot
        with st.spinner("🤖 Bot đang suy nghĩ..."):
            response = vietnamese_food_chatbot.chat(user_input)
        
        # Thêm phản hồi của bot
        st.session_state.chat_history.append({
            "role": "bot", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Auto-play response nếu được bật
        if st.session_state.audio_enabled and st.session_state.auto_play_response:
            try:
                audio_handler.text_to_speech(response, play_audio=True)
            except Exception as e:
                st.warning(f"Không thể phát âm: {str(e)}")
        
        # Clear input và rerun
        st.session_state.user_input = ""
        st.experimental_rerun()

if __name__ == "__main__":
    ui = StreamlitUI()
    ui.render_sidebar()
    ui.render_main_content()