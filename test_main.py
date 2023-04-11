import unittest
import os
import tempfile
from flask import json
from main import app, db, User, ContactDetail, Face, Event
import datetime


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(self.db_path)
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.app.post('/login', data=dict(username="test_user", password="test_password"), follow_redirects=True)
        self.assertIn(b'Home', response.data)

    def test_logout(self):
        self.app.post('/login', data=dict(username="test_user", password="test_password"), follow_redirects=True)
        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_view_contacts(self):
        response = self.app.get('/view_contacts')
        self.assertEqual(response.status_code, 200)

    def test_add_contact(self):
        response = self.app.post('/add_contact', data=dict(name="John Doe", email="john.doe@example.com", phone="1234567890"), follow_redirects=True)
        self.assertIn(b'John Doe', response.data)

    def test_view_faces(self):
        response = self.app.get('/view_faces')
        self.assertEqual(response.status_code, 200)

    def test_view_events(self):
        response = self.app.get('/view_events')
        self.assertEqual(response.status_code, 200)

    def test_create_tables(self):
        with app.app_context():
            db.drop_all()
            db.create_all()

            user = User(username='test_user', password='test_password')
            db.session.add(user)
            db.session.commit()

            contact = ContactDetail(name='test_contact', email='test_contact@example.com', phone='9876543210', user_id=user.id)
            db.session.add(contact)
            db.session.commit()

            event = Event(name='test_event', date=datetime.date(2023, 4, 11), event='Entering', image_path='./Events/20230227-121817308.jpg')
            db.session.add(event)
            db.session.commit()

            self.assertEqual(User.query.count(), 1)
            self.assertEqual(ContactDetail.query.count(), 1)
            self.assertEqual(Event.query.count(), 1)

if __name__ == '__main__':
    unittest.main()
