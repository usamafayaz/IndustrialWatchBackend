import cv2 as cv
import os
import numpy as np
import tensorflow as tf
from mtcnn.mtcnn import MTCNN
from keras_facenet import FaceNet
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import pickle

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class FacenetTraining:
    def __init__(self):
        self.directory = os.path.join('EmployeeImages')
        self.target_size = (160, 160)
        self.detector = MTCNN()
        self.embedder = FaceNet()
        self.X = []
        self.Y = []

    def extract_face(self, filename):
        img = cv.imread(filename)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        faces = self.detector.detect_faces(img)
        if faces:
            x, y, w, h = faces[0]['box']
            x, y = abs(x), abs(y)
            face = img[y:y + h, x:x + w]
            face_arr = cv.resize(face, self.target_size)
            return face_arr
        else:
            return None

    def load_faces(self, dir):
        FACES = []
        for im_name in os.listdir(dir):
            try:
                path = os.path.join(dir, im_name)
                single_face = self.extract_face(path)
                if single_face is not None:
                    FACES.append(single_face)
            except Exception as e:
                print(f"Error loading image {im_name}: {e}")
                pass
        return FACES

    def load_classes(self):
        self.X = []
        self.Y = []
        for sub_dir in os.listdir(self.directory):
            path = os.path.join(self.directory, sub_dir)
            FACES = self.load_faces(path)
            labels = [sub_dir for _ in range(len(FACES))]
            print(f"Loaded successfully: {len(labels)}")
            self.X.extend(FACES)
            self.Y.extend(labels)
        return np.asarray(self.X), np.asarray(self.Y)

    def get_embedding(self, face_img):
        face_img = face_img.astype('float32')
        face_img = np.expand_dims(face_img, axis=0)
        yhat = self.embedder.embeddings(face_img)
        return yhat[0]

    def train_model(self):
        print('train ho raha hai ')

        X, Y = self.load_classes()
        EMBEDDED_X = [self.get_embedding(img) for img in X]
        EMBEDDED_X = np.asarray(EMBEDDED_X)

        np.savez_compressed('detection_models/faces_embeddings_done_classes.npz', EMBEDDED_X, Y)

        encoder = LabelEncoder()
        encoder.fit(Y)
        Y = encoder.transform(Y)

        X_train, X_test, Y_train, Y_test = train_test_split(EMBEDDED_X, Y, shuffle=True, random_state=17)

        model = SVC(kernel='linear', probability=True)
        model.fit(X_train, Y_train)

        train_accuracy = accuracy_score(Y_train, model.predict(X_train))
        test_accuracy = accuracy_score(Y_test, model.predict(X_test))

        print(f"Training Accuracy: {train_accuracy}")
        print(f"Testing Accuracy: {test_accuracy}")

        with open('detection_models/svm_model_160x160.pkl', 'wb') as f:
            pickle.dump(model, f)

        return model, encoder
