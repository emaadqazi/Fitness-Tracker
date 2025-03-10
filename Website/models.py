# Database models

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() #Initializing the database via SQlAlchemy

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable = False)

