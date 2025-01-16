from orders.order import Order
from db import db
from datetime import datetime
from product.physical import PhysicalProduct
from product.digital import DigitalProduct

class Purchase(Order):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'purchase'
    }

    def process(self):
        self.status = 'completed'
        self.date = datetime.utcnow()
        return {
            'message': 'Purchase processed successfully',
            'details': {
                'customer_name': self.customer_name,
                'customer_email': self.customer_email,
                'quantity': self.quantity,
                'total_price': self.total_price
            }
        } 