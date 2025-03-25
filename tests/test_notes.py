import pytest
from Website.models import Note, db
from tests.conftest import get_csrf_token

def test_create_note(client, auth):
    auth.login()
    response = client.post('/create_note', data={
        'title': 'Test Note',
        'content': 'This is a test note',
        'tags': 'test,notes'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Note created successfully' in response.data
    assert b'Test Note' in response.data

def test_edit_note(client, auth):
    auth.login()
    # Create a note first
    client.post('/create_note', data={
        'title': 'Original Title',
        'content': 'Original content',
        'tags': 'original'
    })
    
    with client.application.app_context():
        note = Note.query.filter_by(title='Original Title').first()
        note_id = note.id
    
    # Edit the note
    response = client.post(f'/edit_note/{note_id}', data={
        'title': 'Updated Title',
        'content': 'Updated content',
        'tags': 'updated'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Note updated successfully' in response.data
    assert b'Updated Title' in response.data

def test_delete_note(client, auth):
    auth.login()
    # Create a note first
    client.post('/create_note', data={
        'title': 'Test Note',
        'content': 'This is a test note'
    })
    
    with client.application.app_context():
        note = Note.query.filter_by(title='Test Note').first()
        note_id = note.id
    
    # Delete the note
    response = client.get(f'/delete_note/{note_id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Note deleted successfully' in response.data
    assert b'Test Note' not in response.data