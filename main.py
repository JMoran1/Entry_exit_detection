from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for, flash)
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import PasswordType

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite3'
# login_manager = LoginManager()
# login_manager.init_app(app)
db = SQLAlchemy(app)


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


@app.route('/')
def home():
    return render_template('base.html')


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

class ContactsView:
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


contacts_view = ContactsView()

app.add_url_rule('/view_contacts', view_func=contacts_view.view_contacts)
app.add_url_rule('/add_contact', view_func=contacts_view.add_contact, methods=['GET', 'POST'])
app.add_url_rule('/update_contact/<pk>', view_func=contacts_view.update_contact, methods=['GET', 'POST'])
app.add_url_rule('/delete_contact/<pk>', view_func=contacts_view.delete_contact)


if __name__ == '__main__':
    app.run(debug=True)
