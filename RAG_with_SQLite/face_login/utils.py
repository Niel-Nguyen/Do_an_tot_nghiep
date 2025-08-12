import face_recognition
import pickle
import os

FACE_DB = "F:\\d2l_do_an\\d2l-en\\do_an_tot_nghiep\\Do_an_tot_nghiep\\Do_an_tot_nghiep\\RAG_CHINH - mới nhất - có menu - ver2\\face_login\\face_database.pkl"

def load_faces():
    if os.path.exists(FACE_DB):
        with open(FACE_DB, "rb") as f:
            return pickle.load(f)
    return {}

def save_faces(data):
    with open(FACE_DB, "wb") as f:
        pickle.dump(data, f)

def find_face(face_encoding, known_faces):
    if not known_faces:
        return None

    encodings = list(known_faces.values())
    names = list(known_faces.keys())

    matches = face_recognition.compare_faces(encodings, face_encoding)
    distances = face_recognition.face_distance(encodings, face_encoding)

    if True in matches:
        best_idx = distances.argmin()
        return names[best_idx]
    return None
