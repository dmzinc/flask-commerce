import pytest
from user import User, UserFactory
from db import db

def test_create_user(app):
    with app.app_context():
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        user = UserFactory.create_user('customer', **user_data)
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.type == 'customer'
        assert user.verify_password('password123')

def test_create_duplicate_user(app):
    with app.app_context():
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        user1 = UserFactory.create_user('customer', **user_data)
        db.session.add(user1)
        db.session.commit()
        
        with pytest.raises(Exception):
            user2 = UserFactory.create_user('customer', **user_data)
            db.session.add(user2)
            db.session.commit() 