from orders.order import Order
from orders.purchase import Purchase
from db import db
from datetime import datetime
from product.physical import PhysicalProduct
from product.digital import DigitalProduct
from utils.logger import logger, cart_logger

class Cart(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_cart')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

    def check_stock(self, product):
        """Check if product is in stock and quantity is available"""
        if isinstance(product, PhysicalProduct):
            if product.stock == 0:
                return False, "Product out of stock"
            elif product.stock < self.quantity:
                return False, f"Only {product.stock} items available"
            return True, "Stock available"
        return True, "Digital product"

    def process(self):
        """Process the cart item"""
        self.status = 'in_cart'
        self.date = datetime.utcnow()
        return {
            'message': 'Item added to cart',
            'details': {
                'product_id': self.product_id,
                'quantity': self.quantity,
                'total_price': self.total_price
            }
        }

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_user_cart(cls, user_id):
        """Get cart items for a user"""
        return cls.query.filter_by(user_id=user_id, status='in_cart').all()

    @classmethod
    def add_to_cart(cls, product_id, quantity, user_id):
        """Add item to cart"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return None, "Product not found"

            cart_item = cls.query.filter_by(
                product_id=product_id,
                user_id=user_id,
                status='in_cart'
            ).first()

            if cart_item:
                cart_item.quantity += quantity
                cart_item.total_price = product.price * cart_item.quantity
            else:
                cart_item = cls(
                    product_id=product_id,
                    quantity=quantity,
                    total_price=product.price * quantity,
                    user_id=user_id,
                    status='in_cart'
                )

            # Check stock availability
            stock_available, message = cart_item.check_stock(product)
            if not stock_available:
                return None, message

            if not cart_item.id:
                db.session.add(cart_item)
            db.session.commit()
            
            return cart_item, "Item added to cart successfully"
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @classmethod
    def clear_cart(cls, user_id):
        """Clear user's cart"""
        try:
            cart_items = cls.query.filter_by(
                user_id=user_id,
                status='in_cart'
            ).all()
            
            for item in cart_items:
                db.session.delete(item)
            
            db.session.commit()
            return True, "Cart cleared successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @classmethod
    def complete_purchase(cls, user_id, user_email, user_name):
        """Convert cart items to purchase orders"""
        logger.info(f"User {user_email} attempting to complete purchase")
        
        try:
            cart_items = cls.query.filter_by(user_id=user_id, status='in_cart').all()
            if not cart_items:
                logger.warning(f"No items in cart for user {user_email}")
                return None, "No items in cart"

            purchases = []
            for cart_item in cart_items:
              
                purchase = Purchase(
                    user_id=user_id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    total_price=cart_item.total_price,
                    customer_email=user_email,
                    customer_name=user_name
                )
                
                # Process the purchase
                purchase.process()
                db.session.add(purchase)
                
                # Mark cart item as completed
                cart_item.status = 'completed'
                purchases.append(purchase)
            
            db.session.commit()
            cart_logger.info(
                f"Purchase completed for user {user_email}. "
                f"Total items: {len(purchases)}. "
                f"Purchase IDs: {[p.id for p in purchases]}"
            )
            
            return purchases,
            
        except Exception as e:
            logger.error(f"Error completing purchase for user {user_email}: {str(e)}")
            db.session.rollback()
            return None, str(e) 