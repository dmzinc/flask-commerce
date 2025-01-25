import pytest
import json

def test_add_to_cart(client, app, test_product):
    # Create user
    response = client.post('/users', json={
        'username': 'customer',
        'email': 'customer@example.com',
        'password': 'pass123',
        'user_type': 'customer'
    })
    assert response.status_code == 201

    # Login
    login_response = client.post('/login', json={
        'email': 'customer@example.com',  # Changed from username to email
        'password': 'pass123'
    })
    assert login_response.status_code == 200
    token = json.loads(login_response.data)['token']

    # Add to cart
    cart_response = client.post('/cart/add',
        json={
            'product_id': test_product['id'],
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert cart_response.status_code == 201
    data = json.loads(cart_response.data)
    assert 'cart_item' in data

def test_get_cart(client, app, test_product):
 
    client.post('/users', json={
        'username': 'customer2',
        'email': 'customer2@example.com',
        'password': 'pass123',
        'user_type': 'customer'
    })
    

    login_response = client.post('/login', json={
        'username': 'customer2',
        'password': 'pass123'
    })
    token = json.loads(login_response.data)['token']
    
   
    client.post('/cart/add',
        json={
            'product_id': test_product['id'],  
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    
    response = client.get('/cart',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data

def test_clear_cart(client, app, test_product):
   
    client.post('/users', json={
        'username': 'customer3',
        'email': 'customer3@example.com',
        'password': 'pass123',
        'user_type': 'customer'
    })
    
   
    login_response = client.post('/login', json={
        'username': 'customer3',
        'password': 'pass123'
    })
    token = json.loads(login_response.data)['token']
    
    
    client.post('/cart/add',
        json={
            'product_id': test_product['id'],  
            'quantity': 1
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
 
    response = client.delete('/cart/clear',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data 