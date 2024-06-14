import cv2

from facenet_training import FacenetTraining
from facenet_predict import FaceRecognition

if __name__ == '__main__':
    training_manager = FacenetTraining()

    training_manager.train_model()

    # face_recognition = FaceRecognition()
    # img = cv2.imread("assets/ss.jpg")
    # prediction = face_recognition.predict(img)
    # if prediction is not None:
    #     print(f"Predicted class: {prediction}")
