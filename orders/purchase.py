from orders.order import Order
from db import db
from datetime import datetime
from product.physical import PhysicalProduct
from product.digital import DigitalProduct

class Purchase(Order):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'purchase'
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

    def process(self, product):
        """Process the purchase with stock validation"""
        # Check stock availability
        is_available, message = self.check_stock(product)
        if not is_available:
            return {
                'status': 'failed',
                'message': message
            }

        try:
            # Update stock for physical products
            if isinstance(product, PhysicalProduct):
                product.stock -= self.quantity
                db.session.add(product)

            # Update order status
            self.status = 'completed'
            self.date = datetime.utcnow()
            self.total_price = product.price * self.quantity
            db.session.add(self)
            db.session.commit()

            return {
                'status': 'success',
                'message': 'Purchase processed successfully',
                'details': {
                    'product_name': product.name,
                    'quantity': self.quantity,
                    'total_price': self.total_price,
                    'remaining_stock': getattr(product, 'stock', 'N/A'),
                    'customer_name': self.customer_name,
                    'customer_email': self.customer_email
                }
            }

        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Error processing purchase: {str(e)}'
            } 