import pytest
import sys
import os
from flask import Flask
import json

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db, init_db
from sqlalchemy import text
from main import app as flask_app
from product import ProductFactory

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    # Create admin user
    response = client.post('/users', json={
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'admin123',
        'user_type': 'administrator'
    })
    assert response.status_code == 201
    
    # Login as admin
    response = client.post('/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    assert response.status_code == 200
    return json.loads(response.data)['token']

@pytest.fixture
def test_product(app, client):
    # Create admin user first
    client.post('/users', json={
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'admin123',
        'user_type': 'administrator'
    })
    
    # Login as admin
    login_response = client.post('/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    token = json.loads(login_response.data)['token']
    
    # Create test product
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
    return json.loads(response.data)

@pytest.fixture
def runner(app):
    return app.test_cli_runner() 