# Routes for the application; the app.py file

from flask import render_template, Blueprint, redirect, url_for, flash, request, session, current_app, send_from_directory
from .models import User, ExerciseLog, WeightLog, Photo, Session, ExerciseMedia, Note
from .forms import LoginForm, RegisterForm, WorkoutLog, WeightLogForm, PhotoUploadForm, SessionForm, ExerciseMediaForm
from . import db, bcrypt
from flask_login import login_user, login_required, logout_user, current_user
import os, time
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
        else:
            flash("Your username or password may be incorrect.", "danger")
        
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
        new_user = User(
            username=form.username.data,
            email=form.email.data, 
            password=hashed_password,
            theme='light',
            notification_email=True
        )
        
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
    form = SessionForm()
    
    if form.validate_on_submit():
        new_session = Session(
            title=form.title.data,
            feeling_before=form.feeling_before.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(new_session)
        db.session.commit()
        flash('New session created', 'success')
        return(redirect(url_for('main.dashboard')))
    
    sessions = Session.query.filter_by(user_id=current_user.id,).order_by(Session.date.desc()).all()
    return render_template('dashboard.html', sessions=sessions, form=form)

@main.route('/session_details/<int:session_id>', methods=['GET', 'POST'])
@login_required
def session_details(session_id):
    session = Session.query.get_or_404(session_id)
    
    if session.user_id != current_user.id:
        flash("You do not have permission to view this session.", "danger")
        return redirect(url_for('main.dashboard'))
    
    form = WorkoutLog()
    if form.validate_on_submit():
        new_exercise = ExerciseLog(
            session_id=session_id, 
            exercise=form.exercise.data,
            sets=form.sets.data,
            reps=form.reps.data,
            weight=form.weight.data,
            rpe=form.rpe.data if form.rpe.data else None)
        db.session.add(new_exercise)
        db.session.commit()
        flash("Exercise logged successfully!", "success")
        return redirect(url_for('main.session_details', session_id=session_id))
    
    exercises = ExerciseLog.query.filter_by(session_id=session_id).all()
    return render_template('session_details.html', form=form, session=session, exercises=exercises)
        
@main.route('/update_feeling_after/<int:session_id>', methods=['POST'])
@login_required
def update_feeling_after(session_id):
    session = Session.query.get_or_404(session_id)
    
    if session.user_id != current_user.id:
        flash("You do not have permission to update this session.", "danger")
        return redirect(url_for('main.dashboard'))
    
    feeling_after = request.form.get('feeling_after')
    if feeling_after and feeling_after.isdigit():
        feeling_after = int(feeling_after)
        if 1 <= feeling_after <= 10:
            session.feeling_after = feeling_after 
            db.session.commit()
            flash("Post-workout feeling updated successfully!", "success")
        else:
            flash("Feeling rating must be between 1 and 10.", "danger")
            
    return redirect(url_for('main.session_details', session_id=session_id))

@main.route('/delete_exercise/<int:exercise_id>/<int:session_id>', methods=['POST'])
@login_required
def delete_exercise(exercise_id, session_id):
    exercise = ExerciseLog.query.get_or_404(exercise_id)
    session = Session.query.get_or_404(session_id)
    
    if session.user_id != current_user.id:
        flash("You do not have permission to modify this session.", "danger")
        return redirect(url_for('main.dashboard'))
    
    if exercise.session_id != session_id:
        flash("Invalid request", "danger")
        return redirect(url_for('main.session_details', session_id=session_id))
    
    db.session.delete(exercise)
    db.session.commit()
    
    flash("Exercise deleted successfully!", "success")
    return redirect(url_for('main.session_details', session_id=session_id))

@main.route('/exercise_details/<exercise_id>', methods=['GET', 'POST'])
@login_required
def exercise_details(exercise_id):
    exercise = ExerciseLog.query.get_or_404(exercise_id)
    session = Session.query.get_or_404(exercise.session_id)
    
    if session.user_id != current_user.id:
        flash("You do not have permission to view this exercise.", "danger")
        return redirect(url_for('main.dashboard'))
    
    form = ExerciseMediaForm()
    if form.validate_on_submit():
        media = form.media.data 
        filename = secure_filename(f"{exercise_id}_{int(time.time())}_{media.filename}")
        
        # Determine the media type 
        media_type = 'photo' if media.filename.lower().endswith(('jpg', 'jpeg', 'png')) else 'video'
        
        # Create upload_folder if it does not exist
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'exercises', f'user_{current_user.id}')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Save the media file 
        media_path = os.path.join(upload_folder, filename)
        media.save(media_path)
        
        new_media = ExerciseMedia(
            exercise_id=exercise_id,
            filename=filename,
            media_type=media_type,
            notes=form.notes.data
        )
        
        db.session.add(new_media)
        db.session.commit()
        
        flash("Media uploaded successfully!", "success")
        return redirect(url_for('main.exercise_details', exercise_id=exercise_id))
    
    media_files = ExerciseMedia.query.filter_by(exercise_id=exercise_id).order_by(ExerciseMedia.upload_date.desc()).all()
    
    return render_template('exercise_details.html', form=form, exercise=exercise, media_files=media_files)

@main.route('/exercise_media/<filename>')
@login_required
def exercise_media(filename):
    return send_from_directory(os.path.join(current_app.config['UPLOADED_EXERCISES_DEST'], f'user_{current_user.id}'), filename)

@main.route('/delete_media/<int:media_id>/<int:exercise_id>', methods=['POST'])
@login_required
def delete_media(media_id, exercise_id):
    media = ExerciseMedia.query.get_or_404(media_id)
    exercise = ExerciseLog.query.get_or_404(exercise_id)
    session = Session.query.get_or_404(exercise.session_id)
    
    if session.user_id != current_user.id:
        flash("You do not have permission to delete this media", "danger")
        return redirect(url_for('main.dashboard'))
    
    try:
        media_path = os.path.join(current_app.config['UPLOADED_EXERCISES_DEST'], f'user_{current_user.id}', media.filename)
        if os.path.exists(media_path):
            os.remove(media_path)
        else:
            flash("File not found on server.", "warning")
        
        db.session.delete(media)
        db.session.commit()
        flash("Media deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occured: {str(e)}", "danger")
        
    return redirect(url_for('main.exercise_details', exercise_id=exercise_id))

@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        theme = request.form.get('theme') # Get the form data
        if theme in ['light', 'dark']:
            current_user.theme = theme # Update user settings depending on selected theme
            
        notification_email = 'notification_email' in request.form 
        current_user.notification_email = notification_email 
        
        display_name = request.form.get('display_name')
        if display_name:
            current_user.display_name = display_name 
            
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html')
    

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
        
        upload_folder = os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], f'user_{current_user.id}') # Defining the upload folder
        
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
        photo_path = os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], f'user_{current_user.id}', photo.filename)
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
    return send_from_directory(os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], f'user_{current_user.id}'), filename)

@main.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
    sessions = Session.query.filter_by(user_id=current_user.id).order_by(Session.date.desc()).all()
    
    all_tags = set() # Need to extract unique tags from user's notes
    for note in notes:
        if note.tags:
            for tag in note.tags.split(','):
                all_tags.add(tag.strip())
    
    return render_template('notes.html', notes=notes, sessions=sessions, all_tags=sorted(all_tags))

@main.route('/create_note', methods=['POST'])
@login_required
def create_note():
    title = request.form.get('title')
    content = request.form.get('content')
    tags = request.form.get('tags')
    session_id = request.form.get('session_id') or None 
    
    new_note = Note(
        user_id = current_user.id,
        title=title, 
        content=content, 
        tags=tags,
        session_id=session_id
    )
    
    db.session.add(new_note)
    db.session.commit()
    flash("Note created successfully!", "success")
    return redirect(url_for('main.notes'))

@main.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash("You do not have permission to edit this note", "danger")
        return redirect(url_for('main.notes'))
    
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        note.tags = request.form.get('tags')
        note.session_id = request.form.get('session_id') or None 
        
        db.session.commit()
        flash("Note updated successfully", "success")
        return redirect(url_for('main.notes'))
    
    sessions = Session.query.filter_by(user_id=current_user.id).order_by(Session.date.desc()).all()
    return render_template('edit_note.html', note=note, sessions=sessions)

@main.route('/delete_note/<int:note_id>')
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash("You do not have permission to view this note.", "danger")
        return redirect(url_for('main.notes'))
    
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted successfully!", "success")
    return redirect(url_for('main.notes'))


@main.route('/challenges', methods=['GET', 'POST'])
@login_required
def challenges():
    return render_template('challenges.html')

@main.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    return render_template('analytics.html')