import face_recognition
import numpy as np
import cv2

from .models import Student

# -------------------------------
# 🔥 GLOBAL CACHE (IMPORTANT)
# -------------------------------
KNOWN_FACES = []
IS_LOADED = False


# -------------------------------
# LOAD & ENCODE ALL STUDENTS
# -------------------------------
def load_known_faces():
    global KNOWN_FACES, IS_LOADED

    KNOWN_FACES = []

    students = Student.objects.all()

    for student in students:
        try:
            image = face_recognition.load_image_file(student.image.path)

            # Ensure RGB format
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)

            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:
                KNOWN_FACES.append((student, encodings[0]))
            else:
                print(f"[WARN] No face found in {student.name}")

        except Exception as e:
            print(f"[ERROR] {student.name}: {e}")

    IS_LOADED = True


# -------------------------------
# GET KNOWN FACES (WITH CACHE)
# -------------------------------
def get_known_faces():
    global IS_LOADED

    if not IS_LOADED:
        load_known_faces()

    return KNOWN_FACES


# -------------------------------
# RECOGNIZE FACE FROM FRAME
# -------------------------------
def recognize_face(frame):
    known_faces = get_known_faces()

    if not known_faces:
        print("No known faces loaded")
        return []

    # Resize for speed
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    # Detect faces
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    print("Faces detected:", len(face_encodings))

    recognized_students = []

    known_encodings = [kf[1] for kf in known_faces]

    for face_encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(distances) == 0:
            continue

        best_match_index = np.argmin(distances)
        best_distance = distances[best_match_index]

        # 🔥 Threshold (important)
        if best_distance < 0.6:
            student = known_faces[best_match_index][0]
            recognized_students.append(student)

    return recognized_students


# -------------------------------
# FORCE RELOAD (OPTIONAL)
# -------------------------------
def reload_known_faces():
    global IS_LOADED
    IS_LOADED = False
    load_known_faces()