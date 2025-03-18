# Database models
from . import db 
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin): #Table for db
    id = db.Column(db.Integer, primary_key=True) #Identity for user
    username = db.Column(db.String(20), nullable=False, unique=True) #Username, 20 character limit, cannot be empty 
    password = db.Column(db.String(80), nullable=False) #Password, 80 character limit, cannot be empty
    weight_logs = db.relationship('WeightLog', back_populates="user", lazy=True) # Establishing a connection with WeightLogs so instances of User are accurate with the inputted data 

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise = db.Column(db.String(50), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    rpe = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.today)
    db.relationship('User', backref='logs', lazy=True) #Defines a One-to-Many relationship between Exercise and User
    
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