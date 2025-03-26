import pytest
from Website import create_app, db, bcrypt
from Website.models import User
import re
import os

@pytest.fixture
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    app.template_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Website', 'templates')
    
    with app.app_context():
        db.create_all()
        
        # Create a sample test User
        test_user = User(
            username='testuser',
            email='test@example.com'
        )
        test_user.password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
        db.session.add(test_user)
        db.session.commit()
        
        yield app.test_client()
        db.drop_all()

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='testuser', password='testpassword'):
        response = self._client.get('/login')
        csrf_token = None
        if b'csrf_token' in response.data:
            match = re.search(b'name="csrf_token" type="hidden" value="(.+?)"', response.data)
            if match:
                csrf_token = match.group(1).decode('utf-8')
        
        data = {
            'username': username,
            'password': password
        }
        if csrf_token:
            data['csrf_token'] = csrf_token
            
        return self._client.post('/login', data=data, follow_redirects=True)

    def logout(self):
        return self._client.get('/logout')

@pytest.fixture
def auth(client):
    return AuthActions(client)

# Helper function to extract CSRF tokens
def get_csrf_token(response):
    csrf_token = None
    if b'csrf_token' in response.data:
        match = re.search(b'name="csrf_token" type="hidden" value="(.+?)"', response.data)
        if match:
            csrf_token = match.group(1).decode('utf-8')
    return csrf_token