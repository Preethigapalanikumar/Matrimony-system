import face_recognition

def compare_faces(selfie_path, id_photo_path):
    try:
        selfie_image = face_recognition.load_image_file(selfie_path)
        id_image = face_recognition.load_image_file(id_photo_path)

        selfie_encoding = face_recognition.face_encodings(selfie_image)[0]
        id_encoding = face_recognition.face_encodings(id_image)[0]

        results = face_recognition.compare_faces([id_encoding], selfie_encoding)
        distance = face_recognition.face_distance([id_encoding], selfie_encoding)[0]
        confidence = round((1 - distance) * 100, 2)

        return {'match': results[0], 'confidence': confidence}
    except Exception as e:
        return {'error': str(e)}

def liveness_check(selfie_path):
    # Simulated result
    return "Live"