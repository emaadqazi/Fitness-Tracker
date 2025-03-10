# Routes for the application
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def main_blueprint():
    return render_template('home.html')