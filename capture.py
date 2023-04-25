import cv2 as cv
import numpy as np
import os
import tensorflow as tf
from tensorflow import keras
import threading
import uuid
import sqlite3

face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')

class CaptureFaces(threading.Thread):
    def __init__(self, name, video, path):
        super().__init__()
        self.stop_event = threading.Event()
        self.name = name
        self.video = video
        self.path = path
    
    def add_face(self, image_path):
        conn = sqlite3.connect('./instance/app.sqlite3')
        c = conn.cursor()
        c.execute("INSERT INTO face (name, image_path) VALUES (?,?)", (self.name, image_path))
        conn.commit()
        c.close()
        conn.close()

    def run(self):
        count = 0
        prefix = str(uuid.uuid1())[:4]
        try:
            while not self.stop_event.is_set():
                ret, frame = self.video.read()
                faces = face_cascade.detectMultiScale(frame, 1.3, 5)
                for (x, y, w, h) in faces:
                    print(f"Face detected at {x}, {y}, {w}, {h}")
                    filepath = os.path.join(self.path, self.name, f"{prefix}_{self.name}_{count}.jpg") 
                    cv.imwrite(filepath, frame[y:y+h, x:x+w])
                    self.add_face(filepath)
                    count += 1
                if count > 10:
                    print("Enough faces")
                    self.stop_event.set()
                    # break
        except Exception as e:
            print(f"Error in CaptureFaces thread: {e}")

            

    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":
    pass
