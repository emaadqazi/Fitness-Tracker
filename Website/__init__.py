# This file will be used to initialize the Flask App

from flask import Flask 
from .models import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_tracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    db.init_app(app)
    
    with app.app_context():
        db.create_all() #Creates a database table for our data models
        
    from .views import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app