from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, FileField, SelectField, TextAreaField, DateField
from flask_wtf.file import FileAllowed #For the PhotoUploading feature
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, Regexp, StopValidation, DataRequired, Email
from flask import current_app, flash # To avoid circular imports
from . import db, bcrypt
from .models import User

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"}) # Implementing an email settings feature
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
    exercise_type = SelectField('Exercise Type', choices=[
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('hiit', 'HIIT')
    ], validators=[InputRequired()])
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
    
class SessionForm(FlaskForm):
    title = StringField('Session Title', validators=[DataRequired()])
    feeling_before = IntegerField("How did you feel before (1-10)?", validators=[DataRequired()])
    feeling_after = IntegerField('How did you feel after (1-10)?', validators=[])
    notes = StringField('Session Notes')
    submit = SubmitField('Create Session')

class ExerciseMediaForm(FlaskForm):
    media = FileField('Upload Photo/Video', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'mp4', 'mov'], 'Images and Videos Only!'), 
        DataRequired()
    ])
    notes = StringField('Notes')
    submit = SubmitField('Upload')
    
class SettingsForm(FlaskForm):
    email = StringField('Email', vaidators=[DataRequired(), Email()])
    theme = SelectField('Theme', choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System Default')])
    
    # Implementing password change
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password')
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Save Changes')
    
class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    type = SelectField('Type', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ])
    category = SelectField('Category', choices=[
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('consistency', 'Consistency')
    ])
    goal_value = IntegerField('Goal', validators=[DataRequired()])
    metric = SelectField('Metric', choices=[
        ('reps', 'Repetitions'),
        ('weight', 'Weight (lbs)'),
        ('days', 'Days'),
        ('sessions', 'Sessions')
    ])
    end_date = DateField('End Date', validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')],
        validators=[DataRequired()])
    base_points = IntegerField('Base Points', validators=[DataRequired()], default=100)
    badge_name = StringField('Badge Name', validators=[DataRequired()])
    badge_image = SelectField('Badge Icon', choices=[
        ('🏃', 'Runner'), ('💪', 'Strength'), 
        ('🏋️', 'Weightlifter'), ('🧘', 'Flexibility'),
        ('🎯', 'Target'), ('⭐', 'Star'),
        ('🏅', 'Medal'), ('🏆', 'Trophy')],
        validators=[DataRequired()])
    submit = SubmitField('Create Challenge')

class AnalyticsFilterForm(FlaskForm):
    date_range = SelectField('Date Range', choices=[
        ('7d', 'Last 7 Days'),
        ('30d', 'Last 30 Days'),
        ('90d', 'Last 90 Days'),
        ('1y', 'Last Year')
    ], default='30d')
    
    exercise_type = SelectField('Exercise Type', choices=[
        ('all', 'All Types'),
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('hiit', 'HIIT')
    ], default='all')
    
    challenge_status = SelectField('Challenge Status', choices=[
        ('all', 'All Statuses'),
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
        ('not_started', 'Not Started')
    ], default='all')
    
    submit = SubmitField('Apply Filters')