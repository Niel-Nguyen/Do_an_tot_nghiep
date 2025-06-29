import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
import platform

def record_voice_to_text(timeout=5) -> str:
    """Ghi âm và chuyển giọng nói sang văn bản"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Đang nghe...")
        audio = recognizer.listen(source, timeout=timeout)
    try:
        print("🔎 Đang nhận dạng...")
        text = recognizer.recognize_google(audio, language='vi-VN')
        return text
    except sr.UnknownValueError:
        return "Không nhận dạng được giọng nói."
    except sr.RequestError:
        return "Không thể kết nối dịch vụ nhận dạng."

def speak_text(text: str):
    """Chuyển văn bản thành giọng nói và phát"""
    tts = gTTS(text=text, lang='vi')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        os.system(f"start {fp.name}" if platform.system() == "Windows" else f"afplay {fp.name}")
