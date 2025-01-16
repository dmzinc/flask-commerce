from orders.order import Order
from db import db
from datetime import datetime

class Exchange(Order):
    __tablename__ = 'exchanges'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    new_product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    reason = db.Column(db.String(500))
    
    __mapper_args__ = {
        'polymorphic_identity': 'exchange'
    }

    def process(self):
        self.status = 'processing_exchange'
        self.date = datetime.utcnow()
        return {
            'message': 'Exchange initiated',
            'details': {
                'original_product_id': self.product_id,
                'new_product_id': self.new_product_id,
                'reason': self.reason
            }
        } 