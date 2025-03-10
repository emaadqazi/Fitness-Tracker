# This file will be used to initialize the Flask App

from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
 
db = SQLAlchemy() #Initialize the db, do not assign yet 
bcrypt = Bcrypt() #Initialize without passing app yet

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_tracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    app.config['SECRET_KEY'] = 'secretkey' #Key for Flask sessions
    
    db.init_app(app) # Connect database to the app
    bcrypt.init_app(app) # Passsing app to bcrypt
    
    from .models import User # Import the models
    
    with app.app_context():
        db.create_all() #Creates a database table for our data models
        
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    from .views import main
    app.register_blueprint(main) # Connect blueprint to app so we can use in .views
    
    return app