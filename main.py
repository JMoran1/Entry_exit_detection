from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for, flash, Response)
from flask_sqlalchemy import SQLAlchemy
import os
from train import FaceRecognitionModel
import cv2
import time
from capture import CaptureFaces
import datetime
from detection import InferenceThread
import json
from functools import wraps
from alert import SMSSender
import time
import threading
import sqlite3
import requests
from sqlalchemy import distinct

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite3'
db = SQLAlchemy(app)
FACE_IMAGES = './static/Faces'
EVENT_IMAGES = './static/Events'

cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

global inference_thread


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class ContactDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref(
        'contact_details', lazy=True))


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    event = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)


class Face(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)

def login_required(f):
    """Creates a wrapper to make views require the user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.before_first_request
def create_tables():
    """Create tables in the database before the first request is made."""
    db.create_all()
    # test_user = User(username='user', password='user')
    # db.session.add(test_user)
    # db.session.commit()

    # test_contact = ContactDetail(name='test', email='test', phone='test', user_id=1)
    # db.session.add(test_contact)
    # db.session.commit()

    # Create a test event
    # test_event = Event(name='Jacob', date=datetime.date(2023,4,11), event='Entering', image_path='./Events/20230227-121817308.jpg')
    # db.session.add(test_event)
    # db.session.commit()



@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user:
            # Hash the user-entered password and compare to the stored hash
                if password == user.password:
                    session['user_id'] = user.id
                    return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/feed')
def video_feed():
    """Streams the frames from the camera to the web page."""
    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/change_times', methods=['GET','POST'])
def change_times():
    with open('config.json', 'r') as json_file:
            data = json.load(json_file)
    times = {
        'timer': data['timer'],
        'min_time': data['min_time'],
        'max_time': data['max_time']
    }
    if request.method == 'POST':
        data['timer'] = request.form['timer']
        data['min_time'] = request.form['min_time']
        data['max_time'] = request.form['max_time']
        with open('config.json', 'w') as json_file:
            json.dump(data, json_file)
        return redirect(url_for('settings'))
    return render_template('change_times.html', times=times)

class ContactsViews:
    @login_required
    def view_contacts(self):
        contacts = ContactDetail.query.all()
        print(contacts)

        return render_template('view_contacts.html', contacts=contacts)

    @login_required
    def add_contact(self):
        if request.method == 'POST':
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            contact_details = ContactDetail(name=name, email=email, phone=phone)
            db.session.add(contact_details)
            db.session.commit()
            return redirect(url_for('view_contacts'))
        else:
            return render_template('add_contact.html', contact=None)

    @login_required
    def update_contact(self, pk):
        contact = ContactDetail.query.filter_by(id=pk).first()
        if request.method == 'POST':
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']

            contact.name = name
            contact.phone = phone
            contact.email = email
            db.session.commit()
            return redirect(url_for('view_contacts'))
        else:
            return render_template('add_contact.html', contact=contact)

    @login_required
    def delete_contact(self, pk):
        contact = ContactDetail.query.filter_by(id=pk).first()
        db.session.delete(contact)
        db.session.commit()
        return redirect(url_for('view_contacts'))
    
class FaceViews:
    @login_required
    def view_faces(self):
        faces = Face.query.all()
        return render_template('view_faces.html', faces=faces)
    
    @login_required
    def add_face(self):
        if request.method == 'POST':
            name = request.form['name']

            for uploaded_file in request.files.getlist('file'):
                if uploaded_file.filename != '':
                    print(uploaded_file.filename)

                    if os.path.isdir(os.path.join(FACE_IMAGES, name)):
                        print('Directory already exists')
                    else:
                        os.mkdir(os.path.join(FACE_IMAGES, name))
                        print('Directory created')

                    image_path = os.path.join(
                        FACE_IMAGES, name, uploaded_file.filename)
                    uploaded_file.save(image_path)

                    face = Face(name=name, image_path=image_path)
                    db.session.add(face)
                    db.session.commit()
                    return redirect(url_for('view_faces'))
        else:
            return render_template('add_face.html', face=None)
        
    @login_required
    def update_face(self, pk):
        face = Face.query.filter_by(id=pk).first()
        if request.method == 'POST':
            name = request.form['name']

            for uploaded_file in request.files.getlist('file'):
                if uploaded_file.filename != '':
                    image_path = os.path.join(
                        FACE_IMAGES, name, uploaded_file.filename)
                    
                    face.name = name
                    face.image_path = image_path
                    db.session.commit()
                    return redirect(url_for('view_faces'))
        else:
            return render_template('add_face.html', face=face)
        
    @login_required
    def delete_face(self, pk):
        """Remove the image from the file system and delete the record from the database."""
        face = Face.query.filter_by(id=pk).first()
        os.remove(face.image_path)
        db.session.delete(face)
        db.session.commit()
        return redirect(url_for('view_faces'))

class ComputerVisionViews:
    @app.route('/start_inference')
    @login_required
    def start_inference():
        global inference_thread
        inference_thread = InferenceThread(video=cap, model_name=get_model_name())
        inference_thread.start()
        return redirect(url_for('home'))

    @app.route('/stop_inference')
    @login_required
    def stop_inference():
        print('Stopping inference')
        global inference_thread
        inference_thread.stop()
        return redirect(url_for('home'))

    @app.route('/start_training')
    @login_required
    def start_training():
        names = db.session.query(Face.name).distinct().all()
        training_model = FaceRecognitionModel(num_classes=(len(names) + 1))
        # training_model = FaceRecognitionModel(num_classes=4)
        name, history = training_model.train(FACE_IMAGES)
        print(history.history['accuracy'][-1])
        print(name)
        evaluate_model(name, history)
        return redirect(url_for('view_faces'))
    
    @app.route('/capture_face_images', methods=['GET', 'POST'])
    @login_required
    def capture_face_images():
        if request.method == 'POST':
            name = request.form['name']
            image_capture = CaptureFaces(name=name, video=cap, path=FACE_IMAGES)
            image_capture.start()
            image_capture.join()
        else:
            return render_template('capture_face_images.html')
        
        return redirect(url_for('view_faces'))

class EventViews:
    @app.route('/view_events')
    @login_required
    def view_events():
        # Show all events in the database for the current day
        events = Event.query.all()
        return render_template('view_events.html', events=events)
    
class AlertSystem:
    @app.route('/start_alert_system/<name>')
    def start_alert_system(name):
        with open('config.json', 'r') as json_file:
            data = json.load(json_file)

        # Get a list of all names in the Faces table
        unique_names = db.session.query(distinct(User.name)).all()
        unique_names = [name[0] for name in unique_names]
        unique_names.append('Unknown')
        unique_names = sorted(unique_names)

        timer = data['timer']
        min_time = data['min_time']
        max_time = data['max_time']
        time = datetime.datetime.now()

        # Check if the current time is within the time range
        if time.hour >= min_time and time.hour <= max_time:
            # Start timer
            alert_thread = threading.Thread(target=alert_timer, args=(timer,))
            alert_thread.start()
        else:
            requests.get('http://127.0.0.1:5000/send_alert')
            return "Left in excluded time"


        return "Success"
    
    @app.route('/send_alert')
    def send_alert():
        sms = SMSSender()
        # Get all contacts from the database
        contacts = ContactDetail.query.all()
        for contact in contacts:
            sms.send_sms(contact.phone_number, f"Alert! Person has left the house!")
        return "Success"

contacts_view = ContactsViews()
face_view = FaceViews()
computer_vision_view = ComputerVisionViews()
event_view = EventViews()


app.add_url_rule('/view_contacts', view_func=contacts_view.view_contacts)
app.add_url_rule('/add_contact', view_func=contacts_view.add_contact, methods=['GET', 'POST'])
app.add_url_rule('/update_contact/<pk>', view_func=contacts_view.update_contact, methods=['GET', 'POST'])
app.add_url_rule('/delete_contact/<pk>', view_func=contacts_view.delete_contact)
app.add_url_rule('/view_faces', view_func=face_view.view_faces)
app.add_url_rule('/add_face', view_func=face_view.add_face, methods=['GET', 'POST'])
app.add_url_rule('/update_face/<pk>', view_func=face_view.update_face, methods=['GET', 'POST'])
app.add_url_rule('/delete_face/<pk>', view_func=face_view.delete_face)

def evaluate_model(name, history):
    if history.history['accuracy'][-1] > 0.7:
        with open('config.json', 'r') as json_file:
            data = json.load(json_file)
            data['current_model'] = name
            data['accuracy_score'] = history.history['accuracy'][-1]

        with open('config.json', 'w') as json_file:
            json.dump(data, json_file)

def get_model_name():
    with open('config.json', 'r') as json_file:
        data = json.load(json_file)
        return data['current_model']
    
def has_returned(time):
    conn = sqlite3.connect('./instance/app.sqlite3')
    c = conn.cursor()
    c.execute("SELECT * FROM Event WHERE date > ?", (time,))
    events = c.fetchall()
    c.close()
    conn.close()
    
    for event in events:
        if event[2] == 'Entered':
            return True
        
    return False
    
def alert_timer(timer):
    current_time = datetime.datetime.now()
    returned = False
    time.sleep(timer)
    # Get a list of all events after the current time
    returned = has_returned(current_time)
    
    if not returned:
        requests.get('http://127.0.0.1:5000/send_alert')




if __name__ == '__main__':
    app.run(debug = True,)
    # for i in range(13000, 18000):
    #     try:
    #         app.run(debug = True, host='0.0.0.0', port = i)
    #         break
    #     except OSError as e:
    #         print("Port {i} not available".format(i))