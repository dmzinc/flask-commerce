from orders.order import Order
from db import db
from datetime import datetime

class Exchange(Order):
    __tablename__ = 'exchanges'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    new_product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    reason = db.Column(db.String(500))
    customer_email = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False)
    original_purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    admin_notes = db.Column(db.String(500))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    rejected_at = db.Column(db.DateTime)
    
    __mapper_args__ = {
        'polymorphic_identity': 'exchange'
    }

    def process(self):
        self.status = 'pending_approval'
        self.date = datetime.utcnow()
        return {
            'message': 'Exchange initiated',
            'details': {
                'original_product_id': self.product_id,
                'new_product_id': self.new_product_id,
                'reason': self.reason,
                'customer_name': self.customer_name,
                'customer_email': self.customer_email
            }
        } 