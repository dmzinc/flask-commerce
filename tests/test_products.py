import pytest
import json

def test_create_physical_product(client, app):
   
    client.post('/users', json={
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'admin123',
        'user_type': 'administrator'
    })
    
   
    login_response = client.post('/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    token = json.loads(login_response.data)['token']
    
 
    response = client.post('/products', 
        json={
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 99.99,
            'product_type': 'physical',
            'weight': 1.5,
            'stock': 10
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'name' in data
    assert data['name'] == 'Test Product'
    assert 'description' in data
    assert data['description'] == 'Test Description'
    assert 'details' in data
    assert data['details']['stock'] == 10
    assert data['details']['weight'] == 1.5

def test_get_products(client):
    response = client.get('/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'products' in data 