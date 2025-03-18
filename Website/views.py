# Routes for the application; the app.py file

from flask import render_template, Blueprint, redirect, url_for, flash, request, session, current_app, send_from_directory
from .models import User, ExerciseLog, WeightLog, Photo
from .forms import LoginForm, RegisterForm, WorkoutLog, WeightLogForm, PhotoUploadForm
from . import db, bcrypt
from flask_login import login_user, login_required, logout_user, current_user
import os 
from werkzeug.utils import secure_filename

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
    form = RegisterForm() #Initialize a registration form from the forms.py
    
    if request.method == 'GET':
        session.pop('_flashes', None)
    
    if form.validate_on_submit(): #Whenever user fills in form, we hash password
        print("Form validated!") #DEBUG STATEMENT
        
        existing_user = db.session.execute(db.select(User).filter_by(username=form.username.data)).scalar()
        #Case #1 - user exists and password matches username 
        if existing_user and bcrypt.check_password_hash(existing_user.password, form.password.data):
            print("User already exists and password inputted matches, redirecting to login page!") #DEBUG STATEMENT
            return redirect(url_for('main.login')) # Redirect user to login page if account already exists 
        
        #Case #2 - user exists, password does not match 
        elif existing_user: 
            flash("That username already exists. Please try again.", "danger")
            print("Username already exists, password is incorrect!") #DEBUG STATEMENT
            return render_template('register.html', form=form)
        
        #Case #3 - need to add user to database
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') #Decode the hash
        new_user = User(username=form.username.data, password=hashed_password)
        
        try:
            db.session.add(new_user) # Add new user to data base
            db.session.commit()
            flash("Account created successfully! Please log in.", "success")
            print("User successfully added!") #DEBUG STATEMENT
            return redirect(url_for('main.login')) # Redirect user to Login
        except Exception as e:
            print("Database error:", str(e))
            db.session.rollback()
            flash("An error occured. Please try again.", "danger")
    
    else:
        print("Form did not validate!")
        print(form.errors)
    
    return render_template('register.html', form=form)

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = WorkoutLog()
    
    if form.validate_on_submit():
        new_log = ExerciseLog(user_id=current_user.id, 
                              exercise=form.exercise.data,
                              sets=form.sets.data,
                              reps=form.reps.data,
                              weight=form.weight.data,
                              rpe=form.rpe.data if form.rpe.data else None)
        db.session.add(new_log)
        db.session.commit()
        flash("Exercise logged successfully!", "success")
        return redirect(url_for('main.dashboard'))
        
    logs = ExerciseLog.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', form=form, logs=logs)

@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/weightlog', methods=['GET', 'POST'])
@login_required
def weightlog():
    form = WeightLogForm()
    
    if form.validate_on_submit():
        new_weight_log = WeightLog(user_id=current_user.id, weight=form.weight.data)
        db.session.add(new_weight_log)
        db.session.commit()
        flash("Weight logged successfully!", "success")
        return redirect(url_for('main.weightlog'))
    
    # Filters WeightLog table and retrieves records where user_id matches current_user.id
    # .all() finds ALL entries associated with x user; logs will reflect these in the .html page
    logs = WeightLog.query.filter_by(user_id=current_user.id).all()
    return render_template('weight_log.html', form=form, logs=logs)

@main.route('/progressphotos', methods=['GET', 'POST'])
@login_required
def progressphotos():
    form = PhotoUploadForm()
    
    if form.validate_on_submit():
        photo = form.photo.data # Getting the photo data from the form
        filename = secure_filename(photo.filename) # Generate a secure filename
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', f'user_{current_user.id}') # Defining the upload folder
        
        if not os.path.exists(upload_folder): # If folder does not exist, create it
            os.makedirs(upload_folder)
        
        photo_path = os.path.join(upload_folder, filename)
        photo.save(photo_path)
        
        # Create a new photo record and assign it to the current user 
        new_photo = Photo(user_id=current_user.id, filename=filename)
        db.session.add(new_photo)
        db.session.commit()
        
        flash('Photo uploaded successfully!', 'success')
        return redirect(url_for('main.progressphotos'))
    
    photos_list = Photo.query.filter_by(user_id=current_user.id).all()
    return render_template('progress_photos.html', form=form, photos=photos_list)

@main.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id) # Need to find the photo from the database
    
    if photo.user_id != current_user.id:
        flash('You do not have permission to delete this photo.', 'danger')
        return redirect(url_for('main.progressphotos'))
    
    try:
        photo_path = os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], photo.filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)
            flash('Photo deleted successfully', 'success')
        else:
            flash('Photo not found!', 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        
    db.session.delete(photo)  # Delete from database
    db.session.commit()
    
    return redirect(url_for('main.progressphotos'))

@main.route('/uploaded_photo/<filename>')
def uploaded_photo(filename):
    # Serve the photo from the UPLOADED_PHOTOS_DEST folder (static/uploads)
    return send_from_directory(current_app.config['UPLOADED_PHOTOS_DEST'], filename)

@main.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    return render_template('notes.html')

@main.route('/challenges', methods=['GET', 'POST'])
@login_required
def challenges():
    return render_template('challenges.html')

@main.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    return render_template('analytics.html')