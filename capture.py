import cv2 as cv
import numpy as np
import os
import tensorflow as tf
from tensorflow import keras
import threading

face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')

class CaptureFaces(threading.Thread):
    def __init__(self, name, video):
        super().__init__()
        self.stop_event = threading.Event()
        self.name = name
        self.video = video

    def run(self):
        count = 0
        try:
            while not self.stop_event.is_set():
                ret, frame = self.video.read()
                faces = face_cascade.detectMultiScale(frame, 1.3, 5)
                for (x, y, w, h) in faces:
                    print(f"Face detected at {x}, {y}, {w}, {h}")
                    count += 1
                if count > 50:
                    print("Enough faces")
                    # break
        except Exception as e:
            print(f"Error in CaptureFaces thread: {e}")

            

    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":
    pass
