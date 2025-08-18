import face_recognition
import cv2
import base64
import numpy as np
from .utils import load_faces, save_faces, find_face

def decode_base64_image(image_b64):
    header, encoded = image_b64.split(",", 1)
    img_data = base64.b64decode(encoded)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def recognize_user(image_b64: str) -> str:
    known_faces = load_faces()
    image = decode_base64_image(image_b64)

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb)

    if encodings:
        return find_face(encodings[0], known_faces)
    return None

def register_user(name: str, image_b64: str):
    known_faces = load_faces()
    image = decode_base64_image(image_b64)

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb)

    if encodings:
        known_faces[name] = encodings[0]
        save_faces(known_faces)
