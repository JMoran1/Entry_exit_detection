from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for, flash)
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import PasswordType

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite3'
login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))


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


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        
        # if user and user.password.hash(bytes(password, 'utf-8')):

        #     session['user_id'] = user.id
        #     return redirect(url_for('home'))

        # flash('Invalid username or password')
        # return redirect(url_for('login'))

        if user:
                print(user.password)
            # Hash the user-entered password and compare to the stored hash
                hashed_password = user.password.hash(password)
                print(hashed_password)
                # if hashed_password == user.password:
                    # session['user_id'] = user.id
                return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
