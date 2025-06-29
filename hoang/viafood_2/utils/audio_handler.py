import os
import io
import tempfile
from typing import Optional
import streamlit as st
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
import pygame
import threading
import time

class AudioHandler:
    """Xử lý Text-to-Speech và Speech-to-Text"""
    
    def __init__(self, language='vi'):
        self.language = language
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Khởi tạo pygame cho phát âm thanh
        try:
            pygame.mixer.init()
            self.pygame_available = True
        except:
            self.pygame_available = False
            print("Pygame không khả dụng, sẽ sử dụng phương pháp khác")
    
    def text_to_speech(self, text: str, play_audio: bool = True) -> Optional[bytes]:
        """
        Chuyển văn bản thành giọng nói
        
        Args:
            text: Văn bản cần chuyển đổi
            play_audio: Có phát âm thanh ngay không
            
        Returns:
            bytes: Dữ liệu audio dạng bytes
        """
        try:
            if not text or not text.strip():
                return None
            
            # Tạo đối tượng gTTS
            tts = gTTS(text=text, lang=self.language, slow=False)
            
            # Lưu vào buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Phát âm thanh nếu được yêu cầu
            if play_audio:
                self.play_audio_from_bytes(audio_buffer.getvalue())
            
            return audio_buffer.getvalue()
            
        except Exception as e:
            print(f"Lỗi Text-to-Speech: {e}")
            return None
    
    def play_audio_from_bytes(self, audio_bytes: bytes):
        """Phát âm thanh từ bytes"""
        try:
            # Tạo file tạm thời
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name
            
            if self.pygame_available:
                # Sử dụng pygame
                pygame.mixer.music.load(tmp_file_path)
                pygame.mixer.music.play()
                
                # Đợi phát xong
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            else:
                # Sử dụng pydub (fallback)
                audio = AudioSegment.from_mp3(tmp_file_path)
                play(audio)
            
            # Xóa file tạm
            os.unlink(tmp_file_path)
            
        except Exception as e:
            print(f"Lỗi khi phát audio: {e}")
    
    def speech_to_text(self, audio_data=None, duration: int = 5) -> Optional[str]:
        """
        Chuyển giọng nói thành văn bản
        
        Args:
            audio_data: Dữ liệu audio (nếu có)
            duration: Thời gian ghi âm (giây)
            
        Returns:
            str: Văn bản được nhận dạng
        """
        try:
            if audio_data is None:
                # Ghi âm từ microphone
                with self.microphone as source:
                    print("Đang điều chỉnh nhiễu...")
                    self.recognizer.adjust_for_ambient_noise(source)
                    
                    print(f"Bắt đầu ghi âm trong {duration} giây...")
                    audio_data = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            # Nhận dạng giọng nói
            print("Đang nhận dạng...")
            text = self.recognizer.recognize_google(audio_data, language=self.language)
            
            return text
            
        except sr.WaitTimeoutError:
            print("Timeout: Không nghe thấy âm thanh")
            return None
        except sr.UnknownValueError:
            print("Không thể nhận dạng được giọng nói")
            return None
        except sr.RequestError as e:
            print(f"Lỗi khi gọi Google Speech Recognition: {e}")
            return None
        except Exception as e:
            print(f"Lỗi Speech-to-Text: {e}")
            return None
    
    def record_audio_streamlit(self) -> Optional[str]:
        """Ghi âm và nhận dạng giọng nói trong Streamlit"""
        try:
            # Sử dụng audio_recorder component nếu có
            # Hoặc fallback về phương pháp ghi âm truyền thống
            return self.speech_to_text()
            
        except Exception as e:
            print(f"Lỗi khi ghi âm: {e}")
            return None
    
    def create_audio_player_html(self, audio_bytes: bytes) -> str:
        """Tạo HTML player cho audio"""
        import base64
        
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        html = f'''
        <audio controls autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            Trình duyệt không hỗ trợ phát audio.
        </audio>
        '''
        
        return html
    
    def is_microphone_available(self) -> bool:
        """Kiểm tra microphone có khả dụng không"""
        try:
            with self.microphone as source:
                pass
            return True
        except:
            return False
    
    def get_available_microphones(self) -> list:
        """Lấy danh sách microphone khả dụng"""
        try:
            return sr.Microphone.list_microphone_names()
        except:
            return []

class StreamlitAudioComponents:
    """Các component audio cho Streamlit"""
    
    @staticmethod
    def audio_recorder_button(key: str = "audio_recorder") -> Optional[bytes]:
        """Button ghi âm với audio_recorder (nếu có)"""
        try:
            # Thử import audio_recorder
            from st_audiorec import st_audiorec
            
            wav_audio_data = st_audiorec()
            return wav_audio_data
            
        except ImportError:
            # Fallback nếu không có st_audiorec
            if st.button("🎤 Bắt đầu ghi âm", key=key):
                return b"placeholder"  # Placeholder để trigger xử lý
            return None
    
    @staticmethod
    def text_to_speech_button(text: str, audio_handler: AudioHandler, key: str = "tts_button"):
        """Button Text-to-Speech"""
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("🔊", help="Nghe âm thanh", key=key):
                # Tạo audio
                audio_bytes = audio_handler.text_to_speech(text, play_audio=False)
                
                if audio_bytes:
                    # Hiển thị player
                    html_player = audio_handler.create_audio_player_html(audio_bytes)
                    st.markdown(html_player, unsafe_allow_html=True)
        
        with col2:
            st.write(text)

# Global instance
audio_handler = AudioHandler()