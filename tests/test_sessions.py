import pytest
from Website.models import Session
from Website import db
from tests.conftest import get_csrf_token

def test_create_session(client, auth):
    auth.login()
    
    response = client.get('/dashboard')
    csrf_token = get_csrf_token(response)
    
    data = {
        'title': 'Test Workout',
        'feeling_before': 5,
        'notes': 'Test session notes'
    }
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    response = client.post('/dashboard', data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'New session created' in response.data

def test_session_details_view(client, auth):
    auth.login()
    
    with client.application.app_context():
        new_session = Session(
            title='Test Workout',
            feeling_before=7,
            notes='Test session notes',
            user_id=1
        )
        db.session.add(new_session)
        db.session.commit()
        
        session = Session.query.filter_by(title='Test Workout').first()
        session_id = session.id
    
    response = client.get(f'/session_details/{session_id}')
    assert response.status_code == 200
    assert b'Test Workout' in response.data

def test_log_exercise(client, auth):
    auth.login()
    
    with client.application.app_context():
        new_session = Session(
            title='Test Workout',
            feeling_before=7,
            notes='Test session notes',
            user_id=1
        )
        db.session.add(new_session)
        db.session.commit()
        
        session = Session.query.filter_by(title='Test Workout').first()
        session_id = session.id
    
    response = client.get(f'/session_details/{session_id}')
    csrf_token = get_csrf_token(response)
    
    data = {
        'exercise': 'Bench Press',
        'sets': 3,
        'reps': 10,
        'weight': 225,
        'rpe': 8
    }
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    response = client.post(f'/session_details/{session_id}', data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Exercise logged successfully' in response.data
    assert b'Bench Press' in response.data