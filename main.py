from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for, flash, Response)
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import PasswordType
import os
from train import FaceRecognitionModel
import cv2
import time
from capture import CaptureFaces
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite3'
# login_manager = LoginManager()
# login_manager.init_app(app)
db = SQLAlchemy(app)
FACE_IMAGES = './Faces'

# cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


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
    test_event = Event(name='Jacob', date=datetime.date(2023,4,11), event='Entering', image_path='./Events/20230227-121817308.jpg')
    db.session.add(test_event)
    db.session.commit()



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user:
                print(user.password)
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


class ContactsViews:
    def view_contacts(self):
        contacts = ContactDetail.query.all()
        print(contacts)

        return render_template('view_contacts.html', contacts=contacts)

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

    def delete_contact(self, pk):
        contact = ContactDetail.query.filter_by(id=pk).first()
        db.session.delete(contact)
        db.session.commit()
        return redirect(url_for('view_contacts'))
    
class FaceViews:
    def view_faces(self):
        faces = Face.query.all()
        return render_template('view_faces.html', faces=faces)
    
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
        
    def delete_face(self, pk):
        """Remove the image from the file system and delete the record from the database."""
        face = Face.query.filter_by(id=pk).first()
        os.remove(face.image_path)
        db.session.delete(face)
        db.session.commit()
        return redirect(url_for('view_faces'))

class ComputerVisionViews:
    def start_inference():
        pass

    def stop_inference():
        pass

    @app.route('/start_training')
    def start_training():
        names = db.session.query(Face.name).distinct().all()
        training_model = FaceRecognitionModel(num_classes=(len(names) + 1))
        model = training_model.train(FACE_IMAGES)
        return redirect(url_for('view_faces'))
    
    @app.route('/capture_face_images')
    def capture_face_images():
        image_capture = CaptureFaces(name="Jacob", video=cap)
        image_capture.start()
        print('Starting image capture')
        time.sleep(5)
        print('Stopping image capture')
        image_capture.stop()
        image_capture.join()
        return redirect(url_for('view_faces'))

class EventViews:
    @app.route('/view_events')
    def view_events():
        # Show all events in the database for the current day
        events = Event.query.all()
        return render_template('view_events.html', events=events)

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



if __name__ == '__main__':
    app.run(debug = True,)
    # for i in range(13000, 18000):
    #     try:
    #         app.run(debug = True, host='0.0.0.0', port = i)
    #         break
    #     except OSError as e:
    #         print("Port {i} not available".format(i))