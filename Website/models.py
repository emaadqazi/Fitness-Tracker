# Database models
from . import db 
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin): #Table for db
    id = db.Column(db.Integer, primary_key=True) #Identity for user
    username = db.Column(db.String(20), nullable=False, unique=True) #Username, 20 character limit, cannot be empty 
    password = db.Column(db.String(80), nullable=False) #Password, 80 character limit, cannot be empty 

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
