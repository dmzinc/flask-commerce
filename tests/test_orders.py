import pytest
import json
from datetime import datetime
import jwt

def test_get_orders_as_admin(client, admin_token, test_product):
    response = client.get('/orders',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'orders' in data

def test_get_orders_as_customer(client, app, test_product):
  
    client.post('/users', json={
        'username': 'customer4',
        'email': 'customer4@example.com',
        'password': 'pass123',
        'user_type': 'customer'
    })
    
   
    login_response = client.post('/login', json={
        'username': 'customer4',
        'password': 'pass123'
    })
    token = json.loads(login_response.data)['token']
    
    decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    user_id = decoded_token['user_id']
    
    
    cart_response = client.post('/cart/add',
        json={
            'product_id': test_product['id'], 
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert cart_response.status_code == 201

    
    complete_response = client.post('/cart/complete',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert complete_response.status_code == 200
    
    
    response = client.get('/orders',
        headers={'Authorization': f'Bearer {token}'}
    )
    
  
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'orders' in data
   
    for order in data['orders']:
        assert order['details']['product_id'] == test_product['id']