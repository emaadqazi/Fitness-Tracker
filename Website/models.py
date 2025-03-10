# Database models
from . import db 
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask import current_app # To avoid circular imports

class User(db.Model, UserMixin): #Table for db
    id = db.Column(db.Integer, primary_key=True) #Identity for user
    username = db.Column(db.String(20), nullable=False, unique=True) #Username, 20 character limit, cannot be empty 
    password = db.Column(db.String(80), nullable=False) #Password, 80 character limit, cannot be empty 
    
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        with current_app.app_context(): # Ensures access to database
            existing_user = db.session.execute(db.select(User).filter_by(username=username.data)).scalar()
            if existing_user:
                raise ValidationError("That username already exists. Please choose a different one.")
        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")