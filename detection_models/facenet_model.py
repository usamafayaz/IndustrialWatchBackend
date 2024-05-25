# import cv2 as cv
# import os
# import matplotlib.pyplot as plt
# import tensorflow as tf
# from mtcnn.mtcnn import MTCNN
# import numpy as np
# from keras_facenet import FaceNet
# from sklearn.preprocessing import LabelEncoder
# from sklearn.model_selection import train_test_split
# from sklearn.svm import SVC
# from sklearn.metrics import accuracy_score
# import pickle
#
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
#
# class FACELOADING:
#     def __init__(self, directory):
#         self.directory = directory
#         self.target_size = (160, 160)
#         self.X = []
#         self.Y = []
#         self.detector = MTCNN()
#
#     def extract_face(self, filename):
#         img = cv.imread(filename)
#         img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
#         faces = self.detector.detect_faces(img)
#         if faces:
#             x, y, w, h = faces[0]['box']
#             x, y = abs(x), abs(y)
#             face = img[y:y+h, x:x+w]
#             face_arr = cv.resize(face, self.target_size)
#             return face_arr
#         else:
#             return None
#
#     def load_faces(self, dir):
#         FACES = []
#         for im_name in os.listdir(dir):
#             try:
#                 path = os.path.join(dir, im_name)
#                 single_face = self.extract_face(path)
#                 if single_face is not None:
#                     FACES.append(single_face)
#             except Exception as e:
#                 print(f"Error loading image {im_name}: {e}")
#                 pass
#         return FACES
#
#     def load_classes(self):
#         for sub_dir in os.listdir(self.directory):
#             path = os.path.join(self.directory, sub_dir)
#             FACES = self.load_faces(path)
#             labels = [sub_dir for _ in range(len(FACES))]
#             print(f"Loaded successfully: {len(labels)}")
#             self.X.extend(FACES)
#             self.Y.extend(labels)
#         return np.asarray(self.X), np.asarray(self.Y)
#
#     def plot_images(self):
#         plt.figure(figsize=(18, 16))
#         for num, image in enumerate(self.X):
#             ncols = 3
#             nrows = len(self.Y) // ncols + 1
#             plt.subplot(nrows, ncols, num + 1)
#             plt.imshow(image)
#             plt.axis('off')
#
# faceloading = FACELOADING("EmployeeImages")
# X, Y = faceloading.load_classes()
#
# embedder = FaceNet()
#
# def get_embedding(face_img):
#     face_img = face_img.astype('float32')
#     face_img = np.expand_dims(face_img, axis=0)
#     yhat = embedder.embeddings(face_img)
#     return yhat[0]
#
# EMBEDDED_X = []
#
# for img in X:
#     EMBEDDED_X.append(get_embedding(img))
#
# EMBEDDED_X = np.asarray(EMBEDDED_X)
#
# np.savez_compressed('faces_embeddings_done_classes.npz', EMBEDDED_X, Y)
#
# encoder = LabelEncoder()
# encoder.fit(Y)
# Y = encoder.transform(Y)
#
# X_train, X_test, Y_train, Y_test = train_test_split(EMBEDDED_X, Y, shuffle=True, random_state=17)
#
# model = SVC(kernel='linear', probability=True)
# model.fit(X_train, Y_train)
#
# ypreds_train = model.predict(X_train)
# ypreds_test = model.predict(X_test)
#
# detector = MTCNN()
#
# t_im = cv.imread("test_image.png")
# t_im = cv.cvtColor(t_im, cv.COLOR_BGR2RGB)
# result = detector.detect_faces(t_im)
# print("Detection result:", result)
# if result:
#     x, y, w, h = result[0]['box']
#     x, y = abs(x), abs(y)
#     t_im = t_im[y:y+h, x:x+w]
#     t_im = cv.resize(t_im, (160, 160))
#     print("Processed image shape:", t_im.shape)
#     test_im = get_embedding(t_im)
#     test_im = np.expand_dims(test_im, axis=0)
#     ypreds = model.predict(test_im)
#     print("Predicted class:", encoder.inverse_transform(ypreds))
# else:
#     print("No face detected.")
#
# with open('svm_model_160x160.pkl', 'wb') as f:
#     pickle.dump(model, f)
import cv2

from facenet_training import FacenetTraining
from facenet_predict import FaceRecognition

if __name__ == '__main__':
    # training_manager = FacenetTraining()
    #
    # training_manager.train_model()

    face_recognition = FaceRecognition()
    img = cv2.imread("assets/raahim.jpg")
    prediction = face_recognition.predict(img)
    if prediction is not None:
        print(f"Predicted class: {prediction}")
