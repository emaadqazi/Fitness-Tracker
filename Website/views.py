# Routes for the application; the app.py file

from flask import render_template, Blueprint, redirect, url_for
from .models import RegisterForm, User, LoginForm
from . import db, bcrypt
from flask_login import login_user, login_required, logout_user

main = Blueprint("main", __name__) # Create blueprint for main routes; we can access app

@main.route('/')
def main_blueprint():
    return render_template('home.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard')) # Redirect to home 
        
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit(): #Whenever user fills in form, we hash password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') #Decode the hash
        new_user = User(username=form.username.data, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('main.login')) #Redirect to login page whenever we fill out form
        except Exception as e:
            print("Database error:", str(e))
            db.session.rollback()
    
    return render_template('register.html', form=form)

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))