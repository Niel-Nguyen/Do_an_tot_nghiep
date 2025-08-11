import cv2
import face_recognition
import pickle
import os

# Đường dẫn file database
DATABASE_PATH = "F:\\d2l_do_an\\d2l-en\\do_an_tot_nghiep\\Do_an_tot_nghiep\\Do_an_tot_nghiep\\RAG_CHINH - mới nhất - có menu - ver2\\face_login\\face_database.pkl"

# Load database hiện có
def load_database():
    if os.path.exists(DATABASE_PATH) and os.path.getsize(DATABASE_PATH) > 0:
        with open(DATABASE_PATH, 'rb') as f:
            return pickle.load(f)
    return {}

# Lưu database vào file
def save_database(database):
    with open(DATABASE_PATH, 'wb') as f:
        pickle.dump(database, f)

# Hàm đăng ký khuôn mặt
def register_face(name):
    print(f"[INFO] Đang bật camera để đăng ký khuôn mặt cho: {name}")
    cap = cv2.VideoCapture(0)

    face_encoding = None
    frame_count = 0
    encodings = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Không thể đọc từ camera.")
            break

        # Thu nhỏ khung hình để xử lý nhanh hơn
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encs = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left) in face_locations:
            # Phóng to lại để hiển thị đúng vị trí
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Lấy encoding đầu tiên nếu có
        if face_encs:
            encodings.append(face_encs[0])
            frame_count += 1

        cv2.imshow("Dang ky khuon mat - Bam 'q' de luu", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if encodings:
        # Lấy trung bình các encoding để tăng độ ổn định
        face_encoding = sum(encodings) / len(encodings)
        database = load_database()
        database[name] = face_encoding
        save_database(database)
        print(f"[SUCCESS] Đã lưu khuôn mặt cho {name}")
    else:
        print("[WARNING] Không tìm thấy khuôn mặt để đăng ký.")

if __name__ == "__main__":
    name = input("Nhập tên người cần đăng ký khuôn mặt: ")
    register_face(name)
