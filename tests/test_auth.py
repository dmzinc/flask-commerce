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
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user_type' in data

def test_login_invalid_credentials(client):
    response = client.post('/login', json={
        'email': 'nonexistent@example.com',
        'password': 'wrong'
    })
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data 