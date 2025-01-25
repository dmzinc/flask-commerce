from flask import Flask, request, jsonify, session
from db import db, init_db
from user import User, UserFactory
from product import Product, ProductFactory
from orders import Order, OrderFactory, Purchase, Return, Exchange
from orders.cart import Cart
from functools import wraps
import jwt
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from product.physical import PhysicalProduct
from product.digital import DigitalProduct
from sqlalchemy import text
import uuid
import os
from dotenv import load_dotenv
from utils.logger import (
    log_user_operation,
    log_product_operation, 
    log_cart_operation,
    log_order_operation
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Get secret key from environment variable
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# Initialize database
init_db(app)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            print(f"Token validation error: {str(e)}")  # Debug print
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


#Create users
@app.route('/users', methods=['POST'])
@log_user_operation('create_user')
def create_users():
    """
    Create a new user account.

    Method: POST
    URL: http://localhost:5000/users
    Headers: 
        Content-Type: application/json

    Request Body:
    {
        "username": string,    # User's display name
        "email": string,      # User's email address
        "password": string,   # User's password
        "user_type": string   # Either "customer" or "administrator"
    }

    Returns:
    201: {
        "message": "User created successfully",
        "id": int,
        "username": string,
        "email": string,
        "user_type": string
    }
    """
    try:
        data = request.get_json()
        if not isinstance(data, list):
            data = [data]

        created_users = []
        errors = []

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
                db.session.flush() 
                
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

# LOGIN - Authenticate user and get JWT token
@app.route('/login', methods=['POST'])
@log_user_operation('user_login')
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not password:
            return jsonify({'error': 'Password is required'}), 400

        # Try email first, then username
        if email:
            user = User.query.filter_by(email=email).first()
        elif username:
            user = User.query.filter_by(username=username).first()
        else:
            return jsonify({'error': 'Email or username is required'}), 400

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get hashed password from user model
        hashed_password = user.password_hash if hasattr(user, 'password_hash') else user.password

        if not check_password_hash(hashed_password, password):
            return jsonify({'error': 'Invalid password'}), 401

        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, app.config['SECRET_KEY'])

        # Convert bytes to string if needed
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return jsonify({
            'token': token,
            'user_type': user.type
        }), 200

    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

# Get all users
@app.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
    """
    Get all users in the system. Requires administrator privileges.

    Method: GET
    URL: http://localhost:5000/users
    Headers:
        Authorization: Bearer <jwt_token>

    Returns:
    200: {
        "users": [
            {
                "id": int,          # User ID
                "username": string,  # User's display name
                "email": string,     # User's email address
                "type": string      # User type ("customer" or "administrator")
            },
            ...
        ]
    }
    """
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

#  Get user by ID
@app.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """
    Get details for a specific user by their ID. Requires administrator privileges.

    Method: GET
    URL: http://localhost:5000/users/<int:user_id>
    Headers:
        Authorization: Bearer <jwt_token>

    Parameters:
        user_id (int): The ID of the user to retrieve

    Returns:
    200: {
        "user": {
            "id": int,          # User ID
            "username": string,  # User's display name
            "email": string,     # User's email address
            "type": string      # User type ("customer" or "administrator")
        }
    }

    Errors:
    401: {"error": "Token is missing/invalid"}
    403: {"error": "Admin privileges required"}
    404: {"error": "User not found"}
    500: {"error": "Internal server error"}
    """
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'type': user.type
        }
    })

#Update user
@app.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """
    Update a user's information. Users can only update their own information unless they are administrators.

    Method: PUT
    URL: http://localhost:5000/users/<int:user_id>
    Headers:
        Authorization: Bearer <jwt_token>
        Content-Type: application/json

    Parameters:
        user_id (int): The ID of the user to update

    Request Body:
    {
        "username": string,     # Optional - New username
        "email": string,        # Optional - New email address
        "password": string,     # Optional - New password
        "user_type": string     # Optional - New user type (admin only)
    }

    Returns:
    200: {
        "message": "User updated successfully",
        "user": {
            "id": int,          # User ID
            "username": string,  # Updated username
            "email": string,     # Updated email
            "type": string      # User type
        }
    }
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    # Check authorization
    if current_user.id != user_id and current_user.type != 'administrator':
        return jsonify({'error': 'Unauthorized to update this user'}), 403

    # If regular user trying to change user type, deny
    if 'user_type' in data and current_user.type != 'administrator':
        return jsonify({'error': 'Cannot change user type'}), 403

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

#Delete user
@app.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Delete a user account. Admin only.

    Method: DELETE
    URL: http://localhost:5000/users/<user_id>
    Headers:
        Authorization: Bearer <token>

    Returns:
    200: {
        "message": string      # Success message
    }

    Errors:
    401: {"error": "Token is missing/invalid"}
    403: {"error": "Admin privileges required"}
    404: {"error": "User not found"}
    400: {"error": string}     # Other errors
    """
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

#Create products
@app.route('/products', methods=['POST'])
@admin_required
@log_product_operation('create_product')
def create_product(current_user):
    """
    Create one or more new products. Admin only.

    Method: POST
    URL: http://localhost:5000/products
    Headers:
        Authorization: Bearer <token>
        Content-Type: application/json

    Request Body:

    {
        "name": string,           # Product name
        "description": string,    # Product description (optional)
        "price": float,          # Product price
        "product_type": string,  # Either "physical" or "digital"
        
        # For physical products:
        "weight": float,         # Product weight (optional)
        "stock": int,           # Initial stock quantity (optional, default 0)
        
        # For digital products:
        "file_size": float,     # File size in MB (optional)
        "download_link": string  # Download URL (optional)
    }

    Returns:
    201: {                      
        "id": int,
        "name": string,
        "description": string,
        "price": float,
        "type": string,
        "details": object      
    }
    

    Errors:
    400: {"error": string}      # Validation/processing errors
    401: {"error": "Token is missing/invalid"}
    403: {"error": "Admin privileges required"}
    """
    data = request.get_json()
    if isinstance(data, dict):
        data = [data]
    
    created_products = []
    errors = []

    try:
        for product_data in data:
            try:
                
                base_attrs = {
                    'name': product_data['name'],
                    'description': product_data.get('description', ''),
                    'price': product_data['price']
                }
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
                new_product = ProductFactory.create_product(
                    product_type=product_data['product_type'],
                    **base_attrs
                )
                
                db.session.add(new_product)
                db.session.flush() 
                
                product_dict = {
                    'id': new_product.id,
                    'name': new_product.name,
                    'description': new_product.description,
                    'price': new_product.price,
                    'type': new_product.type,
                    'details': new_product.get_details()
                }
                created_products.append(product_dict)
                
            except Exception as e:
                errors.append(f"Error creating product {product_data.get('name')}: {str(e)}")
        
        if created_products:
            db.session.commit()
            response_data = created_products[0] if len(created_products) == 1 else created_products
            return jsonify(response_data), 201
        
        return jsonify({'errors': errors}), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# search product by name
@app.route('/products/search', methods=['GET'])
def search_products():
    """
    Search for products by name.

    Method: GET
    URL: http://localhost:5000/products/search
    Query Parameters:
        q: string - Search term to filter products by name
    
    Returns:
    200: {
        "message": string,
        "products": [
            {
                "name": string,
                "description": string, 
                "price": float,
                "type": string,
                "details": object
            }
        ]
    }
    """
    try:
        # Get search query
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Please provide a search term'}), 400
        
        products = Product.query.filter(
            Product.name.ilike(f'%{query}%')
        ).all()
        
        if not products:
            return jsonify({
                'message': 'No products found',
                'products': []
            }), 200
            
        return jsonify({
            'message': f'Found {len(products)} products',
            'products': [{
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'type': product.type,
                'details': product.get_details()
            } for product in products]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
#Get all products
@app.route('/products', methods=['GET'])
def get_products():
    """
    Get list of all products.

    Method: GET
    URL: http://localhost:5000/products
    Headers: 
        Content-Type: application/json

    Returns:
    200: {
        "products": [
            {
                "id": int,
                "name": string,
                "description": string,
                "price": float, 
                "type": string,
                "details": object
            }
        ]
    }
    """
    try:
        products = Product.query.all()
        return jsonify({
            'products': [{
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'type': product.type,
                'details': product.get_details()
            } for product in products]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#Get product by ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Get product by ID.

    Method: GET
    URL: http://localhost:5000/products/<product_id>
    Headers: 
        Content-Type: application/json

    Returns:
    200: {
        "id": int,
        "name": string,
        "description": string,
        "price": float,
        "type": string,
        "details": object
    }
    """
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'type': product.type,
            'details': product.get_details()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Update product
@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(current_user, product_id):
    """
    Update an existing product. Admin only.

    Method: PUT
    URL: http://localhost:5000/products/<product_id>
    Headers: 
        Content-Type: application/json
        Authorization: Bearer <token>

    Request Body:
    {
        "name": string,           # Optional
        "description": string,    # Optional 
        "price": float,          # Optional
        
        # For physical products:
        "weight": float,         # Optional
        "stock": integer,        # Optional
        
        # For digital products:
        "file_size": float,      # Optional
        "download_link": string   # Optional
    }

    Returns:
    200: {
        "message": string,
        "product": {
            "id": integer,
            "name": string,
            "description": string,
            "price": float,
            "type": string,
            "details": object
        }
    }
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        data = request.get_json()

        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
            
        
        if product.type == 'physical':
            if 'weight' in data:
                product.weight = data['weight']
            if 'stock' in data:
                product.stock = data['stock']
        elif product.type == 'digital':
            if 'file_size' in data:
                product.file_size = data['file_size']
            if 'download_link' in data:
                product.download_link = data['download_link']
                
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'type': product.type,
                'details': product.get_details()
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#Delete product (admin only)
@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(current_user, product_id):
    """
    Delete a product from the catalog. Admin only.

    Method: DELETE
    URL: http://localhost:5000/products/<product_id>
    Headers:
        Authorization: Bearer <token>

    Parameters:
        product_id (int): ID of the product to delete

    Returns:
    200: {
        "message": string,      # Success message
        "product_id": int       # ID of deleted product
    }
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product deleted successfully',
            'product_id': product_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#Create return order
@app.route('/orders/return', methods=['POST'])
@token_required
@log_order_operation('create_return')
def create_return(current_user):
    """
    Create a new return order for a completed purchase.

    Method: POST
    URL: http://localhost:5000/orders/return
    Headers:
        Content-Type: application/json
        Authorization: Bearer <token>

    Request Body:
    {
        "purchase_id": int,
        "reason": string,
        "refund_amount": float
    }

    Returns:
    201: {
        "message": string,
        "return_id": int,
        "status": string,
        "details": {
            "purchase_id": int,
            "product_id": int,
            "reason": string,
            "refund_amount": float,
            "purchase_date": string
        }
    }

    Errors:
    400: {
        "error": "Missing required fields: <fields>"
        "error": "Only completed purchases can be returned"
        "error": "Refund amount cannot exceed original purchase price"
    }
    401: {"error": "Invalid or missing token"}
    403: {"error": "Unauthorized to return this purchase"}
    404: {"error": "Purchase not found"}
    500: {"error": "Internal server error message"}
    """
    data = request.get_json()
    
    try:
        required_fields = ['purchase_id', 'reason', 'refund_amount']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        purchase = Purchase.query.get(data.get('purchase_id'))
        if not purchase:
            return jsonify({'error': 'Purchase not found'}), 404

        if purchase.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized to return this purchase'}), 403

      
        if purchase.status != 'completed':
            return jsonify({'error': 'Only completed purchases can be returned'}), 400

    
        if float(data.get('refund_amount')) > purchase.total_price:
            return jsonify({
                'error': f'Refund amount cannot exceed original purchase price of {purchase.total_price}'
            }), 400

        # Create return order
        return_order = Return(
            user_id=current_user.id,
            product_id=purchase.product_id,
            reason=data.get('reason'),
            refund_amount=data.get('refund_amount'),
            customer_email=current_user.email,
            customer_name=current_user.username,
            purchase_date=purchase.date,
            original_purchase_id=purchase.id
        )
        
        # Process the return
        return_order.process()
        
        db.session.add(return_order)
        db.session.commit()

        return jsonify({
            'message': 'Return request created successfully, waiting for admin approval',
            'return_id': return_order.id,
            'status': 'pending_approval',
            'details': {
                'purchase_id': purchase.id,
                'product_id': purchase.product_id,
                'reason': data.get('reason'),
                'refund_amount': data.get('refund_amount'),
                'purchase_date': purchase.date.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

#Create exchange order
@app.route('/orders/exchange', methods=['POST'])
@token_required
@log_order_operation('create_exchange')
def create_exchange(current_user):
    """
    Create a new exchange order for a completed purchase.

    Method: POST
    URL: http://localhost:5000/orders/exchange
    Headers:
        Content-Type: application/json
        Authorization: Bearer <token>

    Request Body:
    {
        "purchase_id": int,
        "new_product_id": int,
        "reason": string
    }
    """
    data = request.get_json()
    
    try:
        
        required_fields = ['purchase_id', 'new_product_id', 'reason']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

    
        purchase = Purchase.query.get(data.get('purchase_id'))
        if not purchase:
            return jsonify({'error': 'Purchase not found'}), 404

        
        if purchase.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized to exchange this purchase'}), 403

        
        if purchase.status != 'completed':
            return jsonify({'error': 'Only completed purchases can be exchanged'}), 400

      
        new_product = Product.query.get(data.get('new_product_id'))
        if not new_product:
            return jsonify({'error': 'New product not found'}), 404

        # Create exchange order
        exchange_order = Exchange(
            user_id=current_user.id,
            product_id=purchase.product_id,
            new_product_id=new_product.id,
            reason=data.get('reason'),
            customer_email=current_user.email,
            customer_name=current_user.username,
            purchase_date=purchase.date,
            original_purchase_id=purchase.id
        )
        
        # Process the exchange
        exchange_order.process()
        
        db.session.add(exchange_order)
        db.session.commit()

        return jsonify({
            'message': 'Exchange request created successfully, waiting for admin approval',
            'exchange_id': exchange_order.id,
            'status': 'pending_approval',
            'details': {
                'purchase_id': purchase.id,
                'original_product_id': purchase.product_id,
                'new_product_id': new_product.id,
                'reason': data.get('reason'),
                'purchase_date': purchase.date.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Admin approval route for returns
@app.route('/orders/return/<int:return_id>/approve', methods=['POST'])
@admin_required
def approve_return(current_user, return_id):
    """
    Approve or reject a return request. Admin only.

    Method: POST
    URL: http://localhost:5000/orders/return/<return_id>/approve
    Headers: 
        Content-Type: application/json
        Authorization: Bearer <token>

    Request Body:
    {
        "approved": boolean,     # True to approve, False to reject
        "admin_notes": string    # Optional notes about decision
    }

    Returns:
    - 200: Return request processed successfully
        {
            "message": string,
            "return_reference": string,
            "status": string,
            "details": {
                "product_name": string,
                "product_type": string,
                "customer_name": string,      # Only included if approved
                "customer_email": string,     # Only included if approved
                "refund_amount": number,      # Only included if approved
                "admin_notes": string,
                "approved_at"/"rejected_at": string,
                "approved_by"/"rejected_by": string
            }
        }
"""
    try:
        return_order = Return.query.get(return_id)
        if not return_order:
            return jsonify({'error': 'Return order not found'}), 404

        if return_order.status != 'pending_approval':
            return jsonify({'error': 'Return is not pending approval'}), 400

        data = request.get_json()
        approved = data.get('approved', True)
        admin_notes = data.get('admin_notes', '')

     
        product = Product.query.get(return_order.product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if approved:
            
            return_order.status = 'approved'
            return_order.admin_notes = admin_notes
            return_order.approved_by = current_user.id
            return_order.approved_at = datetime.utcnow()

            
            if hasattr(product, 'stock'):
                product.stock += 1
                db.session.add(product)

            db.session.add(return_order)
            db.session.commit()

            return jsonify({
                'message': 'Return approved successfully',
                'return_reference': f'RET-{return_order.id}',
                'status': 'approved',
                'details': {
                    'product_name': product.name,
                    'product_type': product.type,
                    'customer_name': return_order.customer_name,
                    'customer_email': return_order.customer_email,
                    'refund_amount': return_order.refund_amount,
                    'admin_notes': admin_notes,
                    'approved_at': return_order.approved_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'approved_by': current_user.email
                }
            }), 200
        else:
            # Reject return
            return_order.status = 'rejected'
            return_order.admin_notes = admin_notes
            return_order.rejected_by = current_user.id
            return_order.rejected_at = datetime.utcnow()
            
            db.session.add(return_order)
            db.session.commit()

            return jsonify({
                'message': 'Return rejected',
                'return_reference': f'RET-{return_order.id}',
                'status': 'rejected',
                'details': {
                    'product_name': product.name,
                    'product_type': product.type,
                    'admin_notes': admin_notes,
                    'rejected_at': return_order.rejected_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'rejected_by': current_user.email
                }
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Admin approval route for exchanges
@app.route('/orders/exchange/<int:exchange_id>/approve', methods=['POST'])
@admin_required
def approve_exchange(current_user, exchange_id):
    """
    Approve or reject an exchange request. Admin only.

    Method: POST
    URL: http://localhost:5000/orders/exchange/<exchange_id>/approve
    Headers: 
        Content-Type: application/json
        Authorization: Bearer <token>

    Request Body:
    {
        "approved": boolean,     # True to approve, False to reject
        "admin_notes": string    # Optional notes about decision
    }

    Returns:
    - 200: Exchange request processed successfully
        {
            "message": string,
            "exchange_reference": string,
            "status": string,
            "details": {
                "original_product": string,
                "new_product": string,
                "customer_name": string,      # Only included if approved
                "customer_email": string,     # Only included if approved
                "admin_notes": string,
                "approved_at"/"rejected_at": string,
                "approved_by"/"rejected_by": string
            }
        }
"""
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return jsonify({'error': 'Exchange order not found'}), 404

        if exchange.status != 'pending_approval':
            return jsonify({'error': 'Exchange is not pending approval'}), 400

        data = request.get_json()
        approved = data.get('approved', True)
        admin_notes = data.get('admin_notes', '')

        original_product = Product.query.get(exchange.product_id)
        new_product = Product.query.get(exchange.new_product_id)
        
        if not original_product or not new_product:
            return jsonify({'error': 'Products not found'}), 404

        if approved:
           
            exchange.status = 'approved'
            exchange.admin_notes = admin_notes
            exchange.approved_by = current_user.id
            exchange.approved_at = datetime.utcnow()

            
            if hasattr(original_product, 'stock'):
                original_product.stock += 1
                db.session.add(original_product)
            
            if hasattr(new_product, 'stock'):
                new_product.stock -= 1
                db.session.add(new_product)

            db.session.add(exchange)
            db.session.commit()

            return jsonify({
                'message': 'Exchange approved successfully',
                'exchange_reference': f'EXC-{exchange.id}',
                'status': 'approved',
                'details': {
                    'original_product': original_product.name,
                    'new_product': new_product.name,
                    'customer_name': exchange.customer_name,
                    'customer_email': exchange.customer_email,
                    'admin_notes': admin_notes,
                    'approved_at': exchange.approved_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'approved_by': current_user.email
                }
            }), 200
        else:
          
            exchange.status = 'rejected'
            exchange.admin_notes = admin_notes
            exchange.rejected_by = current_user.id
            exchange.rejected_at = datetime.utcnow()
            
            db.session.add(exchange)
            db.session.commit()

            return jsonify({
                'message': 'Exchange rejected',
                'exchange_reference': f'EXC-{exchange.id}',
                'status': 'rejected',
                'details': {
                    'original_product': original_product.name,
                    'new_product': new_product.name,
                    'admin_notes': admin_notes,
                    'rejected_at': exchange.rejected_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'rejected_by': current_user.email
                }
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Add to cart 
@app.route('/cart/add', methods=['POST'])
@token_required
@log_cart_operation('add_to_cart')
def add_to_cart(current_user):
    try:
        data = request.get_json()
        
        # Validate request data
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
            
        quantity = data.get('quantity', 1)
        
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Create cart item
        cart_item = Cart(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
            total_price=product.price * quantity,
            status='in_cart'
        )

        # Check stock availability
        stock_available, message = cart_item.check_stock(product)
        if not stock_available:
            return jsonify({'error': message}), 400

        # Save to database
        db.session.add(cart_item)
        db.session.commit()

        return jsonify({
            'message': 'Item added to cart successfully',
            'cart_item': cart_item.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Add to cart error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

# Get cart contents 
@app.route('/cart', methods=['GET'])
@token_required
def get_cart(current_user):
    """
    Get contents of the user's shopping cart.

    Method: GET
    URL: http://localhost:5000/cart
    Headers:
        Authorization: Bearer <token>

    Returns:
    200: {
        "items": [
            {
                "id": int,          # Cart item ID
                "product_id": int,  # Product ID
                "quantity": int,    # Quantity
                "price": float,     # Unit price
                "total": float      # Total price for this item
            }
        ],
        "total": float             # Total price for all items
    }
    """
    try:
        cart_items = Cart.get_user_cart(current_user.id)
        
        return jsonify({
            'items': [item.to_dict() for item in cart_items],
            'total': sum(item.total_price for item in cart_items)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Clear cart 
@app.route('/cart/clear', methods=['DELETE'])
@token_required
def clear_cart(current_user):
    """
    Clear all items from the user's shopping cart.

    Method: DELETE
    URL: http://localhost:5000/cart/clear
    Headers:
        Authorization: Bearer <token>

    Returns:
    200: {
        "message": string      # Success message
    }
    """
    try:
        success, message = Cart.clear_cart(current_user.id)
        
        if not success:
            return jsonify({'error': message}), 400

        return jsonify({'message': message}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Complete purchase 
@app.route('/cart/complete', methods=['POST'])
@token_required
@log_cart_operation('complete_purchase')
def complete_cart(current_user):
    try:
        # Get all cart items for user
        cart_items = Cart.query.filter_by(
            user_id=current_user.id,
            status='in_cart'
        ).all()

        if not cart_items:
            return jsonify({'error': 'No items in cart'}), 400

        # Create purchase orders
        purchase_ids = []
        for cart_item in cart_items:
            # Create purchase order
            purchase = Purchase(
                user_id=current_user.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                total_price=cart_item.total_price,
                status='completed'
            )
            db.session.add(purchase)
            purchase_ids.append(purchase.id)
            
            # Update product stock if physical
            product = Product.query.get(cart_item.product_id)
            if isinstance(product, PhysicalProduct):
                product.stock -= cart_item.quantity
            
            # Delete cart item
            db.session.delete(cart_item)

        db.session.commit()

        return jsonify({
            'message': 'Purchase completed successfully',
            'purchase_ids': purchase_ids
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Complete cart error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/reset-db', methods=['POST'])
def reset_database():
    try:
        with db.engine.connect() as connection:
            # Drop child tables first
            connection.execute(text("DROP TABLE IF EXISTS cart_items CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS returns CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS exchanges CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS purchases CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS orders CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS physical_products CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS digital_products CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS customers CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS administrators CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            connection.commit()

        # Recreate all tables
        db.create_all()
        
        return jsonify({'message': 'Database reset successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/orders', methods=['GET'])
@token_required
@log_order_operation('get_orders')
def get_orders(current_user):
    """Get orders for the current user or all orders for admin"""
    try:
        # Check if admin by checking the type attribute
        if current_user.type == 'administrator':
            # Admin can see all orders
            purchases = Purchase.query.all()
        else:
            # Customers can only see their own orders
            purchases = Purchase.query.filter_by(user_id=current_user.id).all()

        return jsonify({
            'orders': [purchase.to_dict() for purchase in purchases]
        }), 200

    except Exception as e:
        print(f"Get orders error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
