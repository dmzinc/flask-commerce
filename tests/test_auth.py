import pytest
import json
import jwt

def test_login_success(client, app):
   
    client.post('/users', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'user_type': 'customer'
    })
    
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data

def test_login_invalid_credentials(client):
    response = client.post('/login', json={
        'username': 'nonexistent',
        'password': 'wrong'
    })
    
    assert response.status_code == 401 