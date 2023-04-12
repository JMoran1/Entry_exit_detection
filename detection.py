import os
import threading
import time

import cv2
import numpy as np
import tensorflow as tf
import torch
from matplotlib import pyplot as plt
from tensorflow import keras

model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
# define a video capture object
vid = cv2.VideoCapture(0)
  
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

custom_resnet_model = keras.models.load_model('testModel copy.h5')
prob_model = keras.Sequential([custom_resnet_model, 
                                keras.layers.Softmax()])


def identifyFace(frame):
    face = cv2.resize(frame, (224, 224))
    face = np.expand_dims(face, axis=0)
    predictions = prob_model.predict(face, verbose=1)
    return predictions

def is_in_threshold(y1, y2, frame_height):
    bottom_quarter_threshold = frame_height * 0.75
    return y1 >= bottom_quarter_threshold or y2 >= bottom_quarter_threshold

previous_people_ids = set()

while(True):

    ret, frame = vid.read()
    frame_height = frame.shape[0]
    results = model(frame)
    
    current_people_ids = set()
    # Extract the bounding box coordinates of only the person class
    for i in range(len(results.xyxy[0])):
        if results.xyxy[0][i][5] == 0:
            x1 = int(results.xyxy[0][i][0])
            y1 = int(results.xyxy[0][i][1])
            x2 = int(results.xyxy[0][i][2])
            y2 = int(results.xyxy[0][i][3])

            print(results.xyxy[0][i][4])

            if is_in_threshold(y1, y2, frame_height):
                person_id = 1
                # person_id = int(results.xyxy[0][i][4])
                current_people_ids.add(person_id)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
    #     # Check if people have entered or left the frame
    entered_people = current_people_ids - previous_people_ids
    left_people = previous_people_ids - current_people_ids

    if entered_people:
        print(f"People entered the frame: {entered_people}")
    if left_people:
        print(f"People left the frame: {left_people}")

    # Update the previous_people_ids for the next iteration
    previous_people_ids = current_people_ids
    
    # Detect faces, draws bounding box around face and then identifies the face
    faces = face_cascade.detectMultiScale(frame, 1.3, 5)
    for (x, y, w, h) in faces:
        
        pred = identifyFace(frame[y:y+h, x:x+w])
        pred = np.argmax(pred)

        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)


    # cv2.imshow('frame', np.squeeze(results.render()))
    cv2.imshow('frame', frame)
      

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
  
# After the loop release the cap object
vid.release()
# Destroy all the windows
cv2.destroyAllWindows()