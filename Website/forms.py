from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, FileField
from flask_wtf.file import FileAllowed #For the PhotoUploading feature
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, Regexp, StopValidation, DataRequired
from flask import current_app, flash # To avoid circular imports
from . import db, bcrypt
from .models import User

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(
        validators=[InputRequired(),
            Length(min=6, max=20), #Ensure password is atleast 6 characters, max 20
            Regexp( #Ensures password contains a letter and a number 
                regex=r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$",
                message="Password must contain at least one letter and one number.")],
        render_kw={"placeholder": "Password"})
    
    confirmPassword = PasswordField(validators=[InputRequired(), EqualTo('password', message="Passwords must match")], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField("Register")
    
    def validate_username(self, username): # Method to ensure user is notified if already registered
        with current_app.app_context(): # Ensures access to database; if function is called before app is initialized, we can still acesss (app_context)
            existing_user = db.session.execute(db.select(User).filter_by(username=username.data)).scalar() #.scalar() --> ensures only one record or NONE is returned
            if existing_user: # Query for an existering user, if True, then return error message
                if bcrypt.check_password_hash(existing_user.password, self.password.data):
                    flash("Account already exists, log in.", "info")
                    raise StopValidation
                else:
                    raise ValidationError("That username already exists. Please choose a different one.")
        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")
    
class WorkoutLog(FlaskForm):
    exercise = StringField('Exercise Name: ', validators=[InputRequired()])
    sets = IntegerField('Sets: ', validators=[InputRequired()])
    reps = IntegerField('Reps: ', validators=[InputRequired()])
    weight = FloatField('Weight (lbs): ', validators=[InputRequired()]) #Need to implement toggle feature between lbs/kg
    rpe = IntegerField('RPE', validators=[InputRequired()])
    submit = SubmitField('Log Exercise')
    
class WeightLogForm(FlaskForm):
    weight = FloatField('Weight (lbs)', validators=[DataRequired()])
    submit = SubmitField('Log Weight')
    
class PhotoUploadForm(FlaskForm):
    photo = FileField('Upload Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images Only!'), DataRequired()])
    submit = SubmitField('Upload')