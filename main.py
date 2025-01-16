from flask import Flask, request, jsonify
from db import db, init_db
from user import User, UserFactory
from product import Product, ProductFactory
from orders import Order, OrderFactory, Purchase, Return, Exchange
from functools import wraps
import jwt
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from product.physical import PhysicalProduct
from product.digital import DigitalProduct

app = Flask(__name__)
init_db(app)

# JWT Configuration
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production

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

# Simple product search by name
@app.route('/products/search', methods=['GET'])
def search_products():
    try:
        # Get search query
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Please provide a search term'}), 400
        
        # Search products by name (case-insensitive)
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

# Purchase route - using product name
@app.route('/orders/purchase', methods=['POST'])
def create_purchase():
    data = request.get_json()
    
    try:
        # Validate required fields
        required_fields = ['product_name', 'customer_email', 'customer_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Get product by name
        product_name = data.get('product_name')
        product = Product.query.filter(Product.name.ilike(product_name)).first()
        if not product:
            # Try to find similar products
            similar_products = Product.query.filter(
                Product.name.ilike(f'%{product_name}%')
            ).all()
            if similar_products:
                return jsonify({
                    'error': 'Product not found',
                    'suggestions': [{
                        'name': p.name,
                        'price': p.price,
                        'type': p.type
                    } for p in similar_products]
                }), 404
            return jsonify({'error': 'Product not found'}), 404

        # Create purchase order with customer details
        purchase = OrderFactory.create_order(
            order_type="purchase",
            user_id=data.get('user_id', None),
            product_id=product.id,
            quantity=data.get('quantity', 1),
            status='pending',
            customer_email=data.get('customer_email'),
            customer_name=data.get('customer_name')
        )

        # Process the purchase
        result = purchase.process(product)
        
        if result['status'] == 'success':
            return jsonify(result), 201
        elif result['status'] == 'failed':
            return jsonify(result), 400
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/return', methods=['POST'])
def create_return():
    data = request.get_json()
    
    try:
        # Validate required fields
        required_fields = ['product_name', 'customer_email', 'customer_name', 
                         'purchase_date', 'reason', 'refund_amount']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Get product by name
        product_name = data.get('product_name')
        product = Product.query.filter(Product.name.ilike(product_name)).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Verify purchase exists
        purchase = Purchase.query.filter(
            Purchase.product_id == product.id,
            Purchase.customer_email == data.get('customer_email'),
            Purchase.status == 'completed'
        ).first()

        if not purchase:
            return jsonify({
                'error': 'No completed purchase found for this product with the provided email'
            }), 404

        # Verify return amount doesn't exceed purchase price
        if float(data.get('refund_amount')) > purchase.total_price:
            return jsonify({
                'error': f'Refund amount cannot exceed original purchase price of {purchase.total_price}'
            }), 400

        # Create return order
        return_order = OrderFactory.create_order(
            order_type="return",
            user_id=purchase.user_id,
            product_id=product.id,
            reason=data.get('reason'),
            refund_amount=data.get('refund_amount'),
            status='pending_approval',
            customer_email=data.get('customer_email'),
            customer_name=data.get('customer_name'),
            purchase_date=purchase.date,
            original_purchase_id=purchase.id
        )
        
        db.session.add(return_order)
        db.session.commit()

        return jsonify({
            'message': 'Return request created successfully, waiting for admin approval',
            'return_id': return_order.id,
            'return_reference': f'RET-{return_order.id}',
            'status': 'pending_approval',
            'details': {
                'product_name': product.name,
                'customer_name': data.get('customer_name'),
                'customer_email': data.get('customer_email'),
                'reason': data.get('reason'),
                'refund_amount': data.get('refund_amount'),
                'purchase_date': purchase.date.strftime('%Y-%m-%d %H:%M:%S'),
                'original_purchase_reference': f'PUR-{purchase.id}'
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/orders/exchange', methods=['POST'])
def create_exchange():
    data = request.get_json()
    
    try:
        # Validate required fields
        required_fields = ['original_product_name', 'new_product_name', 
                         'customer_email', 'customer_name', 'reason']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Get original product
        original_product = Product.query.filter(
            Product.name.ilike(data.get('original_product_name'))
        ).first()
        if not original_product:
            return jsonify({'error': 'Original product not found'}), 404

        # Get new product
        new_product = Product.query.filter(
            Product.name.ilike(data.get('new_product_name'))
        ).first()
        if not new_product:
            return jsonify({'error': 'New product not found'}), 404

        # Verify original purchase exists
        purchase = Purchase.query.filter(
            Purchase.product_id == original_product.id,
            Purchase.customer_email == data.get('customer_email'),
            Purchase.status == 'completed'
        ).first()

        if not purchase:
            return jsonify({
                'error': 'No completed purchase found for this product with the provided email'
            }), 404

        # Create exchange order
        exchange = OrderFactory.create_order(
            order_type="exchange",
            user_id=purchase.user_id,
            product_id=original_product.id,
            new_product_id=new_product.id,
            reason=data.get('reason'),
            status='pending_approval',
            customer_email=data.get('customer_email'),
            customer_name=data.get('customer_name'),
            purchase_date=purchase.date,
            original_purchase_id=purchase.id
        )
        
        db.session.add(exchange)
        db.session.commit()

        return jsonify({
            'message': 'Exchange request created successfully, waiting for admin approval',
            'exchange_id': exchange.id,
            'exchange_reference': f'EXC-{exchange.id}',
            'status': 'pending_approval',
            'details': {
                'original_product': original_product.name,
                'new_product': new_product.name,
                'customer_name': data.get('customer_name'),
                'customer_email': data.get('customer_email'),
                'reason': data.get('reason'),
                'purchase_date': purchase.date.strftime('%Y-%m-%d %H:%M:%S'),
                'original_purchase_reference': f'PUR-{purchase.id}'
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Admin approval routes
@app.route('/orders/<int:order_id>/approve', methods=['POST'])
@admin_required
def approve_order(current_user, order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        if order.type not in ['return', 'exchange']:
            return jsonify({'error': 'Only return and exchange orders need approval'}), 400

        if order.status != 'pending_approval':
            return jsonify({'error': 'Order is not pending approval'}), 400

        # Process the approval based on order type
        if order.type == 'return':
            # Update stock for physical products
            product = Product.query.get(order.product_id)
            if isinstance(product, PhysicalProduct):
                product.stock += 1
                db.session.add(product)
            
            order.status = 'approved'
            order.approved_by = current_user.id
            order.approved_at = datetime.utcnow()
            
        elif order.type == 'exchange':
            # Handle stock updates for exchange
            old_product = Product.query.get(order.product_id)
            new_product = Product.query.get(order.new_product_id)
            
            if isinstance(old_product, PhysicalProduct):
                old_product.stock += 1
                db.session.add(old_product)
            
            if isinstance(new_product, PhysicalProduct):
                if new_product.stock > 0:
                    new_product.stock -= 1
                    db.session.add(new_product)
                else:
                    return jsonify({'error': 'New product out of stock'}), 400
            
            order.status = 'approved'
            order.approved_by = current_user.id
            order.approved_at = datetime.utcnow()

        db.session.add(order)
        db.session.commit()

        return jsonify({
            'message': f'{order.type.capitalize()} order approved successfully',
            'order_id': order.id,
            'status': 'approved'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Admin approval route for returns
@app.route('/orders/return/<int:return_id>/approve', methods=['POST'])
@admin_required
def approve_return(current_user, return_id):
    try:
        return_order = Return.query.get(return_id)
        if not return_order:
            return jsonify({'error': 'Return order not found'}), 404

        if return_order.status != 'pending_approval':
            return jsonify({'error': 'Return is not pending approval'}), 400

        data = request.get_json()
        approved = data.get('approved', True)
        admin_notes = data.get('admin_notes', '')

        # Get the product
        product = Product.query.get(return_order.product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if approved:
            # Approve return
            return_order.status = 'approved'
            return_order.admin_notes = admin_notes
            return_order.approved_by = current_user.id
            return_order.approved_at = datetime.utcnow()

            # Update stock only if it's a physical product
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
    try:
        exchange = Exchange.query.get(exchange_id)
        if not exchange:
            return jsonify({'error': 'Exchange order not found'}), 404

        if exchange.status != 'pending_approval':
            return jsonify({'error': 'Exchange is not pending approval'}), 400

        data = request.get_json()
        approved = data.get('approved', True)
        admin_notes = data.get('admin_notes', '')

        # Get both products
        original_product = Product.query.get(exchange.product_id)
        new_product = Product.query.get(exchange.new_product_id)
        
        if not original_product or not new_product:
            return jsonify({'error': 'Products not found'}), 404

        if approved:
            # Approve exchange
            exchange.status = 'approved'
            exchange.admin_notes = admin_notes
            exchange.approved_by = current_user.id
            exchange.approved_at = datetime.utcnow()

            # Update stock for physical products
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
            # Reject exchange
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

# View orders
@app.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    try:
        # Regular users can only see their orders
        # Admins can see all orders
        if current_user.type == 'administrator':
            orders = Order.query.all()
        else:
            orders = Order.query.filter_by(user_id=current_user.id).all()

        return jsonify({
            'orders': [{
                'id': order.id,
                'type': order.type,
                'status': order.status,
                'date': order.date,
                'details': order.get_details()
            } for order in orders]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET - Get all products (no authentication required)
@app.route('/products', methods=['GET'])
def get_products():
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

# GET - Get specific product by ID (no authentication required)
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
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

# UPDATE - Update product (admin only)
@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(current_user, product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        data = request.get_json()
        
        # Update basic attributes
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
            
        # Update type-specific attributes
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

# DELETE - Delete product (admin only)
@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(current_user, product_id):
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

if __name__ == '__main__':
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)
