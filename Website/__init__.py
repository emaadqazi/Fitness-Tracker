# This file will be used to initialize the Flask App

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate 
from dotenv import load_dotenv
import os

db = SQLAlchemy() #Initialize the db, do not assign yet 
bcrypt = Bcrypt() #Initialize without passing app yet

load_dotenv() # Load the .env file to access the keys 

def create_app(test_config=None):
    app = Flask(__name__, template_folder='Website/templates')
    # app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'fitness_tracker.db')}" #Flask knows we are storing fitness_tracker.db in /instance
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.wjzfjoskauarjckfrorj:eHhjYrFfPuptMC5a@aws-0-ca-central-1.pooler.supabase.com:6543/postgres'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    # app.config['SECRET_KEY'] = 'secretkey' #Key for Flask sessions
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    
    if test_config is not None:
        app.config.update(test_config)
    
    app.config['UPLOADS_BASE_DIR'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(app.config['UPLOADS_BASE_DIR'], 'progress_photos')
    app.config['UPLOADED_EXERCISES_DEST'] = os.path.join(app.config['UPLOADS_BASE_DIR'], 'exercises')
    
    migrate = Migrate(app, db)
    db.init_app(app) # Connect database to the app
    bcrypt.init_app(app) # Passsing app to bcrypt
    
    from .models import User, ExerciseLog, WeightLog, ExerciseMedia, Note, Challenge, UserChallenge, UserBadges, Session # Import the models
    
    with app.app_context():
        # Note.__table__.drop(db.engine, checkfirst=True)
        # Note.__table__.create(db.engine)
        # Challenge.__table__.drop(db.engine, checkfirst=True)
        # UserChallenge.__table__.drop(db.engine, checkfirst=True)
        # UserBadges.__table__.drop(db.engine, checkfirst=True)
        # ExerciseLog.__table__.drop(db.engine, checkfirst=True)
        # Session.__table__.drop(db.engine, checkfirst=True)
        # User.__table__.drop(db.engine, checkfirst=True)
        # Challenge.__table__.create(db.engine)
        # UserChallenge.__table__.create(db.engine)
        # UserBadges.__table__.create(db.engine)
        # ExerciseLog.__table__.create(db.engine)
        # Session.__table__.create(db.engine)
        # User.__table__.create(db.engine)
        db.create_all() #Creates a database table for our data models

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    
    @login_manager.user_loader
    def load_user(user_id): 
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_theme():
        from flask_login import current_user
        if current_user.is_authenticated and hasattr(current_user, 'theme'):
            return {'user_theme': current_user.theme}
        return {'user_theme': 'light'} # Default theme 
    
    @app.context_processor
    def inject_supabase_photo_url():
        def supabase_photo_url(filename):
            supabase_url = os.getenv('SUPABASE_URL')
            bucket_name = 'progress-photos'
            return f"{supabase_url}/storage/v1/object/public/{bucket_name}/user_{current_user.id}/{filename}"
        return dict(supabase_photo_url=supabase_photo_url)

    @app.context_processor
    def inject_supabase_exercise_url():
        def supabase_exercise_url(filename):
            supabase_url = os.getenv('SUPABASE_URL')
            bucket_name = 'exercise-media'
            return f"{supabase_url}/storage/v1/object/public/{bucket_name}/user_{current_user.id}/{filename}"
        return dict(supabase_exercise_url=supabase_exercise_url)
    
    from .views import main
    app.register_blueprint(main) # Connect blueprint to app so we can use in .views
    
    return app



        