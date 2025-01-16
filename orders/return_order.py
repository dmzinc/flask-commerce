from orders.order import Order
from db import db
from datetime import datetime

class Return(Order):
    __tablename__ = 'returns'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    reason = db.Column(db.String(500))
    refund_amount = db.Column(db.Float)
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
        'polymorphic_identity': 'return'
    }

    def process(self):
        self.status = 'pending_approval'
        self.date = datetime.utcnow()
        return {
            'message': 'Return initiated',
            'details': {
                'reason': self.reason,
                'refund_amount': self.refund_amount,
                'customer_name': self.customer_name,
                'customer_email': self.customer_email,
                'purchase_date': self.purchase_date.strftime('%Y-%m-%d %H:%M:%S'),
                'original_purchase_id': self.original_purchase_id
            }
        } 