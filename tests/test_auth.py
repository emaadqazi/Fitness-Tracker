import pytest
from Website.models import User
from Website import db
from tests.conftest import get_csrf_token

def test_login_success(client):
    response = client.get('/login')

    csrf_token = get_csrf_token(response)
    
    data = {
        'username': 'testuser',
        'password': 'testpassword'
    }
    if csrf_token:
        data['csrf_token'] = csrf_token
        
    response = client.post('/login', data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'<title>Login</title>' not in response.data
    
def test_login_failure(client):
    response = client.get('/login')
    csrf_token = get_csrf_token(response)
    
    data = {
        'username': 'testuser',
        'password': 'wrongpassword'
    }
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    response = client.post('/login', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' not in response.data

def test_protected_route(client):
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302  # should redirect to login page