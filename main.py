from flask import Flask, request, jsonify
from db import db, init_db
from user.user import User
from user.customer import Customer
from user.admin import Administrator
from user.factory import UserFactory
from product.factory import ProductFactory
from product.product import Product
from functools import wraps
import jwt
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
init_db(app)

# JWT Configuration
app.config['SECRET_KEY'] = 'your-secret-key'  # Move to .env in production

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if current_user.type != 'administrator':
                return jsonify({'error': 'Admin privileges required'}), 403
        except:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if user and user.verify_password(data.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'type': user.type
            }
        })

    return jsonify({'error': 'Invalid username or password'}), 401

# CREATE - Create single or multiple users
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if isinstance(data, dict):
        data = [data]
    
    created_users = []
    errors = []

    try:
        for user_data in data:
            try:
                existing_user = User.query.filter_by(
                    username=user_data['username']
                ).first() or User.query.filter_by(
                    email=user_data['email']
                ).first()

                if existing_user:
                    errors.append(f"User with username {user_data['username']} or email {user_data['email']} already exists")
                    continue

                new_user = UserFactory.create_user(
                    user_type=user_data.get('user_type', 'customer'),
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                
                db.session.add(new_user)
                created_users.append({
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'type': new_user.type
                })
                
            except Exception as e:
                errors.append(f"Error creating user {user_data.get('username')}: {str(e)}")
        
        if created_users:
            db.session.commit()
        
        response = {
            'message': f'Created {len(created_users)} users',
            'users': created_users
        }
        if errors:
            response['errors'] = errors
            
        return jsonify(response), 201 if created_users else 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# READ - Get all users
@app.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
    users = User.query.all()
    return jsonify({
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'type': user.type
            } for user in users
        ]
    })

# READ - Get single user by ID
@app.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'type': user.type
        }
    })

# UPDATE - Update user
@app.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    try:
        if 'username' in data:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Username already taken'}), 400
            user.username = data['username']
            
        if 'email' in data:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already taken'}), 400
            user.email = data['email']
            
        if 'password' in data:
            user.password = data['password']

        db.session.commit()
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'type': user.type
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# DELETE - Delete user
@app.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            'message': f'User {user.username} deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# CREATE - Create single or multiple products
@app.route('/products', methods=['POST'])
@admin_required
def create_product(current_user):
    data = request.get_json()
    if isinstance(data, dict):
        data = [data]
    
    created_products = []
    errors = []

    try:
        for product_data in data:
            try:
                # Base product attributes
                base_attrs = {
                    'name': product_data['name'],
                    'description': product_data.get('description', ''),
                    'price': product_data['price']
                }

                # Add type-specific attributes
                if product_data['product_type'] == 'physical':
                    base_attrs.update({
                        'weight': product_data.get('weight'),
                        'stock': product_data.get('stock', 0)
                    })
                elif product_data['product_type'] == 'digital':
                    base_attrs.update({
                        'file_size': product_data.get('file_size'),
                        'download_link': product_data.get('download_link')
                    })

                # Create product using factory
                new_product = ProductFactory.create_product(
                    product_type=product_data['product_type'],
                    **base_attrs
                )
                
                db.session.add(new_product)
                created_products.append({
                    'id': new_product.id,
                    'name': new_product.name,
                    'description': new_product.description,
                    'price': new_product.price,
                    'type': new_product.type,
                    'details': new_product.get_details()
                })
                
            except Exception as e:
                errors.append(f"Error creating product {product_data.get('name')}: {str(e)}")
        
        if created_products:
            db.session.commit()
        
        response = {
            'message': f'Created {len(created_products)} products',
            'products': created_products
        }
        if errors:
            response['errors'] = errors
            
        return jsonify(response), 201 if created_products else 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
