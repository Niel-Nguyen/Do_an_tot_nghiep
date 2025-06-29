import cv2
import time
from gtts import gTTS
from playsound import playsound
import os
import speech_recognition as sr

def say_vietnamese(text, filename="greeting.mp3"):
    """Chuyển văn bản thành giọng nói tiếng Việt và phát ra"""
    tts = gTTS(text=text, lang='vi')
    tts.save(filename)
    playsound(filename)
    os.remove(filename)  # xóa file sau khi phát xong

def listen_for_command(target_phrases=["chào chatbot"]):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print(" Đang lắng nghe bạn nói...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5)

    try:
        text = recognizer.recognize_google(audio, language='vi-VN')
        print(f"🎤 Bạn nói: {text}")
        for phrase in target_phrases:
            if phrase.lower() in text.lower():
                return phrase
    except sr.UnknownValueError:
        print("Không nghe rõ...")
    except sr.RequestError as e:
        print(f"Lỗi kết nối API Google: {e}")
    
    return None

# Luồng xử lý:
    # Trạng thái 1: Phát hiện khuôn mặt
        # Nếu phát hiện mặt liên tục trong ≥ 5s → chào khách
        # Sau khi chào → chuyển sang trạng thái nghe

    # Trạng thái 2: Lắng nghe người dùng
        # Nếu người dùng nói "chào chatbot" → nói "Bạn cần giúp gì?"
        # Nếu người dùng nói "cảm ơn quý khách đã đến cửa hàng chúng tôi" → nói "Kính chào quý khách!" → quay lại nhận diện mặt


def detect_face_and_greet():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cam = cv2.VideoCapture(0)

    detected_time = None
    last_face_lost_time = None
    greeted = False

    print("Đang đang mở camera ")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Không có camera.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        current_time = time.time()

        if len(faces) > 0:
            if detected_time is None:
                detected_time = current_time
                print("🟢 Phát hiện khuôn mặt - bắt đầu tính thời gian.")
            elif last_face_lost_time:
                # Nếu vừa mới mất mặt nhưng quay lại nhanh < 0.3s thì không reset
                time_lost = current_time - last_face_lost_time
                if time_lost < 0.3:
                    print(f"🟡 Mặt quay lại sau {time_lost:.2f}s < 0.3s → giữ thời gian cũ.")
                else:
                    # Nếu quá 0.3s thì reset hoàn toàn
                    print(f"🔁 Mất mặt quá {time_lost:.2f}s ≥ 0.3s → reset thời gian.")
                    detected_time = current_time  # bắt đầu lại từ lúc này
                last_face_lost_time = None

            # Kiểm tra tổng thời gian từ thời điểm phát hiện ban đầu
            if not greeted and (current_time - detected_time >= 5):
                print("✅ Đã phát hiện người. Đang chào")
                say_vietnamese("Xin chào, tôi là chatbot của nhà hàng ??? , rất vui được phục vụ bạn!")
                greeted = True
                
                # Nghe tiếp giọng nói
                user_command = listen_for_command()
                if user_command:
                    say_vietnamese("Bạn cần giúp gì?")
        else:
            if detected_time is not None and last_face_lost_time is None:
                last_face_lost_time = current_time
                print("🔴 Khuôn mặt biến mất - chờ xem có quay lại không...")
        # Vẽ khung mặt
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Camera - Chatbot Nha Hang ???? ", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_face_and_greet()
