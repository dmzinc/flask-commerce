import pytest
import json

def test_create_user(client):
    response = client.post('/users', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'user_type': 'customer'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Created 1 users'
    assert 'users' in data

def test_create_duplicate_user(client):
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'user_type': 'customer'
    }
    
   
    response1 = client.post('/users', json=user_data)
    assert response1.status_code == 201
    
   
    response2 = client.post('/users', json=user_data)
    assert response2.status_code == 400
    data = json.loads(response2.data)
    assert 'errors' in data 