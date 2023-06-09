import os
import threading
import time
import requests
import uuid
from datetime import datetime
import cv2
import numpy as np
import tensorflow as tf
import torch
from matplotlib import pyplot as plt
from tensorflow import keras
import sqlite3
from collections import deque
import json

model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
  
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

custom_resnet_model = keras.models.load_model('testModel copy.h5')
prob_model = keras.Sequential([custom_resnet_model, 
                                keras.layers.Softmax()])


def is_in_threshold(y1, y2, frame_height):
    bottom_quarter_threshold = frame_height * 0.75
    return y1 >= bottom_quarter_threshold or y2 >= bottom_quarter_threshold

def add_event(name, event, image_path):
    conn = sqlite3.connect('./instance/app.sqlite3')
    c = conn.cursor()
    c.execute("INSERT INTO event (name, date, event, image_path) VALUES (?, ?, ?, ?)", (name, datetime.now(), event, image_path))
    conn.commit()
    c.close()
    conn.close()

def get_names():
    conn = sqlite3.connect('./instance/app.sqlite3')
    c = conn.cursor()
    c.execute("SELECT name FROM face")
    names = c.fetchall()
    c.close()
    conn.close()
    names = [name[0] for name in names]
    names = list(set(names))
    names.append("Unknown")
    return sorted(names)

global previous_people_ids
previous_people_ids = set()

class InferenceThread(threading.Thread):
    def __init__(self, video, model_name):
        super().__init__()
        self.stop_event = threading.Event()
        self.video = video
        self.custom_resnet_model = keras.models.load_model(model_name)
        self.prob_model = keras.Sequential([self.custom_resnet_model, 
                                keras.layers.Softmax()])
        self.frame_buffer = deque(maxlen=10)
        
    def identifyFace(self, frame):
        face = cv2.resize(frame, (224, 224))
        face = np.expand_dims(face, axis=0)
        predictions = self.prob_model.predict(face, verbose=1)
        return predictions

    def run(self):
        count = 0
        entry_detected = False
        entry_count = 0
        while not self.stop_event.is_set():
            ret, frame = self.video.read()
            frame_height = frame.shape[0]
            results = model(frame)
            self.frame_buffer.append(frame)

            if entry_detected:
                entry_count += 1
                if entry_count > 5:
                    entry_detected = False
                    entry_count = 0
                    suffix = str(uuid.uuid1())[:4]
                    cv2.imwrite(f"./static/Events/image{suffix}.jpg", self.frame_buffer[0])
                    add_event("Person", "Entered", f"/Events/image{suffix}.jpg")

            
            current_people_ids = set()
            # Extract the bounding box coordinates of only the person class
            for i in range(len(results.xyxy[0])):
                if results.xyxy[0][i][5] == 0:
                    x1 = int(results.xyxy[0][i][0])
                    y1 = int(results.xyxy[0][i][1])
                    x2 = int(results.xyxy[0][i][2])
                    y2 = int(results.xyxy[0][i][3])

                    if is_in_threshold(y1, y2, frame_height):
                        person_id = int(results.xyxy[0][i][4])
                        current_people_ids.add(person_id)

                    # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
            # Detect faces, draws bounding box around face and then identifies the face
            faces = face_cascade.detectMultiScale(frame, 1.3, 5)
            for (x, y, w, h) in faces:
                
                pred = self.identifyFace(frame[y:y+h, x:x+w])
                pred = np.argmax(pred)

                # cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            # Check if people have entered or left the frame
            global previous_people_ids
            entered_people = current_people_ids - previous_people_ids
            left_people = previous_people_ids - current_people_ids

            if entered_people:
                print(f"People entered the frame: {entered_people}")
                entry_detected = True
            if left_people:
                cv2.imwrite("./static/Events/image.jpg", self.frame_buffer[0])
                print(f"People left the frame: {left_people}")
                names = get_names()
                add_event(f"{names[pred]}", "Left", "/Events/image.jpg")
                
                with open('config.json', 'r') as json_file:
                    data = json.load(json_file)
                    if str(names[pred]) in data['alert_list']:
                        requests.get(f'http://127.0.0.1:5000/start_alert_system/{names[pred]}')

            # Update the previous_people_ids for the next iteration
            previous_people_ids = current_people_ids
            
            
            

    def stop(self):
        self.stop_event.set()

if __name__ == '__main__':
    thread = InferenceThread()
    thread.start()
    time.sleep(30)
    thread.stop()
    thread.join()