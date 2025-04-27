# Routes for the application; the app.py file

from flask import render_template, Blueprint, redirect, url_for, flash, request, session, current_app, send_from_directory
from flask_wtf import FlaskForm
from .models import User, ExerciseLog, WeightLog, Photo, Session, ExerciseMedia, Note, Challenge, UserChallenge
from .forms import LoginForm, RegisterForm, WorkoutLog, WeightLogForm, PhotoUploadForm, SessionForm, ExerciseMediaForm, ChallengeForm, AnalyticsFilterForm
from wtforms.validators import DataRequired
from wtforms import IntegerField, SubmitField
from . import db, bcrypt
from flask_login import login_user, login_required, logout_user, current_user
import os, time, requests
from werkzeug.utils import secure_filename
import datetime 
from sqlalchemy import and_, func

SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')

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
        print("Form validated successfully!")
        new_exercise = ExerciseLog(
            session_id=session_id, 
            exercise=form.exercise.data,
            exercise_type='strength', # Default exercise type value for now 
            sets=form.sets.data,
            reps=form.reps.data,
            weight=form.weight.data,
            rpe=form.rpe.data if form.rpe.data else None)
        db.session.add(new_exercise)
        db.session.commit()
        flash("Exercise logged successfully!", "success")
        return redirect(url_for('main.session_details', session_id=session_id))
    else:
        print("Form did not validate!", form.errors)
    
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
        bucketExercise = 'exercise-media' # Bucket for exercise media 
        
        # Determine the media type 
        media_data = media.read()
        media_type = 'photo' if media.filename.lower().endswith(('jpg', 'jpeg', 'png')) else 'video'
        
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/octet-stream"
        }
        
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucketExercise}/user_{current_user.id}/{filename}"
        response = requests.post(upload_url, headers=headers, data=media_data)
        
        if response.status_code in (200, 201):
            new_media = ExerciseMedia(
                exercise_id=exercise_id,
                filename=filename,
                media_type=media_type,
                notes=form.notes.data
            )
            db.session.add(new_media)
            db.session.commit()
            flash("Media uploaded successfully!", "success")
        else:
            flash('Failed to upload media to Supabase.', 'danger')
            print(response.text)
            print("Upload Error Code:", response.status_code)
        
        return redirect(url_for('main.exercise_details', exercise_id=exercise_id))
    
    media_files = ExerciseMedia.query.filter_by(exercise_id=exercise_id).order_by(ExerciseMedia.upload_date.desc()).all()
    return render_template('exercise_details.html', form=form, exercise=exercise, media_files=media_files)

# @main.route('/exercise_media/<filename>')
# @login_required
# def exercise_media(filename):
#     return send_from_directory(os.path.join(current_app.config['UPLOADED_EXERCISES_DEST'], f'user_{current_user.id}'), filename)

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
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_api_key = os.getenv('SUPABASE_API_KEY')
        bucket = "exercise-media"
        
        delete_url = f"{supabase_url}/storage/v1/object/{bucket}/user_{current_user.id}/{media.filename}"
        
        headers = {
            "apikey": supabase_api_key,
            "Authorization": f"Bearer {supabase_api_key}",
        }
        
        response = requests.delete(delete_url, headers=headers)
        
        if response.status_code not in (200, 204):
            print(f"Failed to delete file from Supabase: {response.text}")
            
        db.session.delete(media)
        db.session.commit()
        flash("Media deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occured:  {str(e)}", "danger")
        
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
        filename = secure_filename(f"user_{current_user.id}_{int(time.time())}_{photo.filename}") # Generate file name based on user_id, time, photo.filename
        bucketStore = 'progress-photos' # Supabase bucket 
        
        photo_data = photo.read() # Read the photo as bytes 
        
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/octet-stream"
        }
        
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucketStore}/user_{current_user.id}/{filename}"
        response = requests.put(upload_url, headers=headers, data=photo_data)
        
        if response.status_code in (200, 201):
            new_photo = Photo(user_id=current_user.id, filename=filename)
            db.session.add(new_photo)
            db.session.commit()
            flash('Photo uploaded successfully!', 'success')
        else:
            flash('Failed to upload photot to Supabase.', 'danger')
            print(response.text)
        
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

# @main.route('/uploaded_photo/<filename>')
# def uploaded_photo(filename):
#     # Serve the photo from the UPLOADED_PHOTOS_DEST folder (static/uploads)
#     return send_from_directory(os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], f'user_{current_user.id}'), filename)

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
    # Getting all active challenges for the user 
    active_pairs = db.session.query(Challenge, UserChallenge).\
        outerjoin(UserChallenge, and_(UserChallenge.challenge_id == Challenge.id, UserChallenge.user_id == current_user.id)).\
            filter(Challenge.end_date > datetime.datetime.today()).all()
            
    # Convert data 
    active_challenges = []
    for challenge, user_challenge in active_pairs:
        challenge_dict = {
            'challenge': challenge,
            'user_challenge': user_challenge,
            'is_joined': user_challenge is not None
        }
        active_challenges.append(challenge_dict)
            
    # Getting all completed challenges for the user 
    completed_pairs = db.session.query(Challenge, UserChallenge).\
        outerjoin(UserChallenge, and_(UserChallenge.challenge_id == Challenge.id, UserChallenge.user_id == current_user.id)).\
            filter(UserChallenge.completed == True).\
                order_by(UserChallenge.completed_date.desc()).all()
    
    # Convert data
    completed_challenges = []
    for challenge, user_challenge in completed_pairs:
        if user_challenge is not None: # Include if user joined it
            challenge_dict = {
                'challenge': challenge,
                'user_challenge': user_challenge,
            }
            completed_challenges.append(challenge_dict)

    return render_template('challenges.html', active_challenges=active_challenges, completed_challenges=completed_challenges)

@main.route('/join_challenge/<int:challenge_id>', methods=['GET', 'POST'])
@login_required 
def join_challenge(challenge_id):
    # Verify challenge exists 
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if user has joined the challenge yet or not
    existing = UserChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if existing:
        flash("You have already joined this challenge", "success")
    else:
        # Create a new user challnege 
        user_challenge = UserChallenge(
            user_id=current_user.id, 
            challenge_id=challenge_id,
            current_value=0,
            completed=False,
        )
        db.session.add(user_challenge)
        db.session.commit()
        flash(f'You have jointed the "{challenge.title}" challenge!', "success")
        
    return redirect(url_for('main.challenges'))
    
@main.route('/create_challenge', methods=['GET', 'POST'])
@login_required
def create_challenge():
    form = ChallengeForm()
    
    if form.validate_on_submit():
        new_challenge = Challenge(
            id=None,
            title=form.title.data,
            description=form.description.data,
            type=form.type.data,
            category=form.category.data,
            goal_value=form.goal_value.data,
            metric=form.metric.data,
            end_date=form.end_date.data,
            difficulty=form.difficulty.data,
            base_points=form.base_points.data,
            badge_name=form.badge_name.data,
            badge_image=form.badge_image.data
        )
        db.session.add(new_challenge)
        db.session.commit()
        flash("New challenge created successfully.", "success")
        return (redirect(url_for('main.challenges')))
    
    return render_template('create_challenge.html', form=form)

@main.route('/update_challenge/<int:user_challenge_id>', methods=['GET', 'POST'])    
def update_challenge(user_challenge_id):
    # Get the user challenge entry if it exists 
    user_challenge = UserChallenge.query.filter_by(
        id=user_challenge_id, 
        user_id=current_user.id
    ).first_or_404()
    
    challenge = user_challenge.challenge # Get corresponding challenge meant to update 
    class UpdateForm(FlaskForm): # Implement update form to update challenge 
        current_value = IntegerField(f'Current progress ({challenge.metric})', validators=[DataRequired()])
        submit = SubmitField('Update Progress')
        
    form = UpdateForm()
    
    if form.validate_on_submit():
        user_challenge.current_value = form.current_value.data # Set user's current challenge value to new form value 
        if user_challenge.current_value >= challenge.goal_value and not user_challenge.completed:
            user_challenge.completed = True # Raise flag to True indicated challenge has been completed
            user_challenge.completed_date = datetime.now() # Record current time
            current_user.points = current_user.points + challenge.points # Update the point system mechanics 
            flash(f'Congratulations! You have completed the challenge and earned {challenge.points} points!', 'success')
            
        db.session.commit()
        return redirect(url_for('main.my_challenges'))
    
    form.current_value.data = user_challenge.current_value 
    return render_template('update_challenge.html', form=form, user_challenge=user_challenge, challenge=challenge)

@main.route('/my_challenges')
@login_required
def my_challenges():
    user_challenges = UserChallenge.query.filter_by(user_id=current_user.id).join(Challenge).all()
    return render_template('my_challenges.html', user_challenges=user_challenges)

@main.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    form = AnalyticsFilterForm()

    # Get the filter parameters
    date_range = request.args.get('date_range', '30d')
    exercise_type = request.args.get('exercise_type', 'all')
    challenge_status = request.args.get('challenge_status', 'all')

    # Calculate the date range
    end_date = datetime.datetime.now()
    if date_range == '7d':
        start_date = end_date - datetime.timedelta(days=7)
    elif date_range == '30d':
        start_date = end_date - datetime.timedelta(days=30)
    elif date_range == '90d':
        start_date = end_date - datetime.timedelta(days=90)
    else:
        start_date = end_date - datetime.timedelta(days=365)

    # Get user growth data
    user_growth = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).filter(
        User.created_at.between(start_date, end_date)
    ).group_by(
        db.func.date(User.created_at)
    ).all()

    # Get workout frequency data
    workout_frequency = db.session.query(
        db.func.strftime('%w', Session.date).label('day'),
        db.func.count(Session.id).label('count')
    ).filter(
        Session.date.between(start_date, end_date),
        Session.user_id == current_user.id
    ).group_by(
        db.func.strftime('%w', Session.date)
    ).all()

    # Get challenge completion data
    challenge_completion = db.session.query(
        UserChallenge.completed,
        db.func.count(UserChallenge.id).label('count')
    ).filter(
        UserChallenge.user_id == current_user.id,
        UserChallenge.created_at.between(start_date, end_date)
    ).group_by(
        UserChallenge.completed
    ).all()

    # Get exercise distribution data
    exercise_distribution = db.session.query(
        ExerciseLog.exercise_type,
        db.func.count(ExerciseLog.id).label('count')
    ).join(
        Session
    ).filter(
        Session.user_id == current_user.id,
        Session.date.between(start_date, end_date)
    ).group_by(
        ExerciseLog.exercise_type
    ).all()

    # Format the data for the charts
    analytics_data = {
        'user_growth': {
            'labels': [str(date) for date, _ in user_growth],
            'data': [count for _, count in user_growth]
        },
        'workout_frequency': {
            'labels': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            'data': [0] * 7  # Initialize with zeros
        },
        'challenge_completion': {
            'labels': ['Completed', 'In Progress', 'Not Started'],
            'data': [0, 0, 0]  # Initialize with zeros
        },
        'exercise_distribution': {
            'labels': ['Strength', 'Cardio', 'Flexibility', 'HIIT'],
            'data': [0, 0, 0, 0]  # Initialize with zeros
        }
    }

    # Update the workout frequency data
    for day, count in workout_frequency:
        analytics_data['workout_frequency']['data'][int(day)] = count

    # Update challenge completion data
    for completed, count in challenge_completion:
        if completed:
            analytics_data['challenge_completion']['data'][0] = count
        else:
            analytics_data['challenge_completion']['data'][1] = count

    # Update exercise distribution data
    for exercise_type, count in exercise_distribution:
        if exercise_type == 'strength':
            analytics_data['exercise_distribution']['data'][0] = count
        elif exercise_type == 'cardio':
            analytics_data['exercise_distribution']['data'][1] = count
        elif exercise_type == 'flexibility':
            analytics_data['exercise_distribution']['data'][2] = count
        elif exercise_type == 'hiit':
            analytics_data['exercise_distribution']['data'][3] = count

    return render_template('analytics.html', form=form, analytics_data=analytics_data)
