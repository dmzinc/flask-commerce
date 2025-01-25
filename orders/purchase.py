from orders.order import Order
from db import db
from datetime import datetime
from product.physical import PhysicalProduct
from product.digital import DigitalProduct

class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='purchases')
    product = db.relationship('Product', backref='purchases')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'details': {
                'product_id': self.product_id,
                'quantity': self.quantity
            }
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