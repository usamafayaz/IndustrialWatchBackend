import cv2 as cv
import os
import matplotlib.pyplot as plt
import tensorflow as tf
from mtcnn.mtcnn import MTCNN
import numpy as np
from keras_facenet import FaceNet
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import pickle
from sklearn.svm import SVC

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class FACELOADING:
    def __init__(self, directory):
        self.directory = directory
        self.target_size = (160, 160)
        self.X = []
        self.Y = []
        self.detector = MTCNN()

    def extract_face(self, filename):
        img = cv.imread(filename)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        x, y, w, h = self.detector.detect_faces(img)[0]['box']
        x, y = abs(x), abs(y)
        face = img[y:y+h, x:x+w]
        face_arr = cv.resize(face, self.target_size)
        return face_arr

    def load_faces(self, dir):
        FACES = []
        for im_name in os.listdir(dir):
            path = os.path.join(dir, im_name)
            if os.path.isfile(path):
                try:
                    single_face = self.extract_face(path)
                    FACES.append(single_face)
                except Exception as e:
                    pass
        return FACES

    def load_classes(self):
        for sub_dir in os.listdir(self.directory):
            path = os.path.join(self.directory, sub_dir)
            if os.path.isdir(path):
                FACES = self.load_faces(path)
                labels = [sub_dir for _ in range(len(FACES))]
                print(f"Loaded successfully: {len(labels)}")
                self.X.extend(FACES)
                self.Y.extend(labels)
        return np.asarray(self.X), np.asarray(self.Y)

    def plot_images(self):
        plt.figure(figsize=(18, 16))
        for num, image in enumerate(self.X):
            ncols = 3
            nrows = len(self.Y) // ncols + 1
            plt.subplot(nrows, ncols, num + 1)
            plt.imshow(image)
            plt.axis('off')

faceloading = FACELOADING("EmployeeImages")
X,Y = faceloading.load_classes()
faceloading.plot_images()
img = cv.imread('EmployeeImages/test_image.png')
img = cv.cvtColor(img, cv.COLOR_BGR2RGB)

embedder = FaceNet()

def get_embedding(face_img):
    face_img = face_img.astype('float32')  # 3D(160x160x3)
    face_img = np.expand_dims(face_img, axis=0)  # 4D (Nonex160x160x3)
    yhat = embedder.embeddings(face_img)
    return yhat[0]  # 512D image (1x1x512)

EMBEDDED_X = []
for img in X:
    EMBEDDED_X.append(get_embedding(img))

EMBEDDED_X = np.asarray(EMBEDDED_X)

encoder = LabelEncoder()
encoder.fit(Y)
Y = encoder.transform(Y)

np.savez_compressed('face_recoganition.npz', EMBEDDED_X, Y)
X_train, X_test, Y_train, Y_test = train_test_split(EMBEDDED_X, Y, shuffle=True, random_state=17)


model = SVC(kernel='linear', probability=True)
model.fit(X_train, Y_train)

ypreds_train = model.predict(X_train)
ypreds_test = model.predict(X_test)

accuracy_score(Y_train, ypreds_train)
accuracy_score(Y_test, ypreds_test)

detector = MTCNN()
results = detector.detect_faces(img)
x,y,w,h = results[0]['box']
img = cv.rectangle(img, (x,y),(x+w,y+h),(0,0,255),30)
face = img[y:y+h, x:x+w]
face = cv.resize(face,(160,160))

# plt.imshow(face)
# plt.show()

test_img = get_embedding(face)
test_img = [test_img]
y_preds = model.predict(test_img)
encoder.inverse_transform(y_preds)