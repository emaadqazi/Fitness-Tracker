# Database models
from . import db 
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin): #Table for db
    id = db.Column(db.Integer, primary_key=True) #Identity for user
    username = db.Column(db.String(20), nullable=False, unique=True) #Username, 20 character limit, cannot be empty 
    email = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False) #Password, 80 character limit, cannot be empty
    created_at = db.Column(db.DateTime, default=datetime.today)
    
    # Settings fields 
    theme = db.Column(db.String(20), default='light')
    notification_email = db.Column(db.Boolean, default=True)
    display_name = db.Column(db.String(50))
    
    sessions = db.relationship('Session', backref='user', lazy=True)
    weight_logs = db.relationship('WeightLog', back_populates="user", lazy=True) # Establishing a connection with WeightLogs so instances of User are accurate with the inputted data 

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.today)
    feeling_before = db.Column(db.Integer) # Scale 1-10
    feeling_after = db.Column(db.Integer) # Scale 1-10
    notes = db.Column(db.Text, nullable=True)
    exercises = db.relationship('ExerciseLog', backref='session', lazy=True)

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    exercise = db.Column(db.String(50), nullable=False)
    exercise_type = db.Column(db.String(20), nullable=False)  # strength, cardio, flexibility, hiit
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    rpe = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.today)
    # db.relationship('User', backref='logs', lazy=True) #Defines a One-to-Many relationship between Exercise and User
    
class WeightLog(db.Model):
    id = db.Column(db.Integer, primary_key=True) # To identify users
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # References user.id
    weight = db.Column(db.Float, nullable=False) # Float value for weight, must have valid entry
    date = db.Column(db.DateTime, default=datetime.today, nullable=False)
    
    # Each WeightLog instance belongs to a User instance; solidifying connection here. 'back_populates' allows changes to be 
    # synchronized so changes from both sides will be consistent amongst each other 
    user = db.relationship('User', back_populates='weight_logs')
    
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.today)
    
    user = db.relationship('User', backref=db.backref('photos', lazy=True))
    
    def __repr__(self): # So we can see the photo 
        return f"<Photo {self.filename}>"
    
class ExerciseMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise_log.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.today)
    # Establish a relationship
    exercise = db.relationship('ExerciseLog', backref='media')
    
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.today)
    updated_at = db.Column(db.DateTime, default=datetime.today, onupdate=datetime.today)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('notes', lazy=True))
    session = db.relationship('Session', backref=db.backref('linked_notes', lazy=True))
    tags = db.Column(db.String(200), nullable=True)
    
class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False) # Daily, weekly or monthly types
    category = db.Column(db.String(50)) # Strength, Cardio, Consistency, etc.
    goal_value = db.Column(db.Integer, nullable=False)
    metric = db.Column(db.String(50)) # How do we want to measure -> reps, weights, days, sessions
    start_date = db.Column(db.DateTime, default=datetime.today)
    end_date = db.Column(db.DateTime, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default='Beginner') # Beginner, Intermediate, Advanced 
    badge_name = db.Column(db.String(50), nullable=False)
    badge_image = db.Column(db.String(200), nullable=False)
    base_points = db.Column(db.Integer, nullable=False)

    def calculate_points(self, completion_percentage):
        difficulty_multiplier = {
            'Beginner': 1,
            'Intermediate': 1.5,
            'Advanced': 2
        }

        if completion_percentage >= 100:
            tier_multiplier = 1.0 # Gold 
        elif completion_percentage >= 75:
            tier_multiplier = 0.75 # Silver
        elif completion_percentage >= 50:
            tier_multiplier = 0.50 # Bronze
        else:
            tier_multiplier = 0.25 # Participant 

        return int(self.base_points * difficulty_multiplier(self.difficulty) * tier_multiplier)
    
class UserChallenge(db.Model): # User's progress on specific challenges 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    current_value = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime, nullable=True)
    achievement_tier = db.Column(db.String(20), nullable=True) # Gold, Silver, Bronze or Participant 
    earned_points = db.Column(db.Integer, default=0)
    badge_earned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.today)

    # Need a way to track progress 
    def update_progress(self, new_value):
        self.current_value = new_value 
        completion_percentage = (new_value / self.challenge.goal_value) * 100

        if completion_percentage >= 100:
            self.achievement_tier = 'Gold'
        elif completion_percentage >= 75:
            self.achievement_tier = 'Silver'
        elif completion_percentage >= 50:
            self.achievement_tier = 'Bronze'
        else:
            self.achievement_tier = 'Participant'

        self.earned_points = self.challenge.calculate_points(completion_percentage)

        if completion_percentage >= 100 and not self.badge_earned:
            self.badge_earned = True 

        return self.achievement_tier, self.earned_points
    
    # Establish relationships
    user = db.relationship('User', backref='challenges') # Backref allows any user instance to access all related UserChallenge instances 
    challenge = db.relationship('Challenge') # One sided relationship; can access Challenge from UserChallenge but not vice versa 

class UserBadges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    badge_name = db.Column(db.String(50), nullable=False)
    badge_image = db.Column(db.String(200), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.today)
    achievement_tier = db.Column(db.String(20), nullable=False)

    user = db.relationship('User', backref=db.backref('badges', lazy=True)) # Creates relationship with UserBadges and Users --> allows for things like user.badges
    challenge = db.relationship('Challenge') # one-way relationship to Challenge