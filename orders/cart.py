from orders.order import Order
from db import db
from datetime import datetime
from product.physical import PhysicalProduct
from product.digital import DigitalProduct

class Cart(Order):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Make user_id required
    
    __mapper_args__ = {
        'polymorphic_identity': 'cart'
    }

    def check_stock(self, product):
        """Check if product is in stock and quantity is available"""
        if isinstance(product, PhysicalProduct):
            if product.stock == 0:
                return False, "Product is out of stock"
            elif product.stock < self.quantity:
                return False, f"Only {product.stock} items available in stock"
            return True, "Product available"
        elif isinstance(product, DigitalProduct):
            return True, "Digital product available"
        return False, "Invalid product type"

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
        """Convert cart item to dictionary"""
        from product.product import Product
        product = Product.query.get(self.product_id)
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': product.name if product else None,
            'quantity': self.quantity,
            'price': product.price if product else None,
            'total_price': self.total_price,
            'status': self.status
        }

    @classmethod
    def get_user_cart(cls, user_id):
        """Get cart items for a user"""
        return cls.query.filter_by(user_id=user_id, status='in_cart').all()

    @classmethod
    def add_to_cart(cls, product_id, quantity, user_id):
        """Add item to cart"""
        from product.product import Product
        product = Product.query.get(product_id)
        if not product:
            return None, "Product not found"

        # Check existing cart item
        cart_item = cls.query.filter_by(
            product_id=product_id,
            status='in_cart',
            user_id=user_id
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

        try:
            if not cart_item.id:
                db.session.add(cart_item)
            db.session.commit()
            return cart_item, "Item added to cart successfully"
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @classmethod
    def clear_cart(cls, user_id):
        """Clear all items from user's cart"""
        try:
            cls.query.filter_by(
                user_id=user_id,
                status='in_cart'
            ).delete()
            db.session.commit()
            return True, "Cart cleared successfully"
        except Exception as e:
            db.session.rollback()
            return False, str(e) 