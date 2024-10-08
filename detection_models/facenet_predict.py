import os.path

import cv2 as cv
import numpy as np
from mtcnn.mtcnn import MTCNN
from keras_facenet import FaceNet
import pickle
from sklearn.preprocessing import LabelEncoder


class FaceRecognition:
    def __init__(self):
        self.model_path = f'detection_models/svm_model_160x160.pkl'
        self.encoder_path = f'detection_models/faces_embeddings_done_classes.npz'
        self.model_path = os.path.abspath(self.model_path)
        self.encoder_path = os.path.abspath(self.encoder_path)
        # Load the trained SVM model
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)

        # Load the label encoder
        data = np.load(self.encoder_path)
        Y = data['arr_1']
        self.encoder = LabelEncoder()
        self.encoder.fit(Y)

        # Initialize MTCNN detector and FaceNet embedder
        self.detector = MTCNN()
        self.embedder = FaceNet()

    def get_embedding(self, face_img):
        face_img = face_img.astype('float32')
        face_img = np.expand_dims(face_img, axis=0)
        yhat = self.embedder.embeddings(face_img)
        return yhat[0]

    def predict(self, image):
        # t_im = cv.imread(image)
        t_im = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        result = self.detector.detect_faces(t_im)
        print("Detection result:", result)

        if result:
            x, y, w, h = result[0]['box']
            x, y = abs(x), abs(y)
            t_im = t_im[y:y + h, x:x + w]
            t_im = cv.resize(t_im, (160, 160))
            print("Processed image shape:", t_im.shape)
            test_im = self.get_embedding(t_im)
            test_im = np.expand_dims(test_im, axis=0)
            predicted_probs = self.model.predict_proba(test_im)
            ypreds = self.model.predict(test_im)
            predicted_class = self.encoder.inverse_transform(ypreds)
            confidence = np.max(predicted_probs)
            print('confidence:', confidence)
            if confidence > 0.3:
                return predicted_class
            else:
                print("Employee not found")
                return None