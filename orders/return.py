from order.order import Order
from db import db
from datetime import datetime

class Return(Order):
    __tablename__ = 'returns'
    id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    reason = db.Column(db.String(500))
    refund_amount = db.Column(db.Float)
    
    __mapper_args__ = {
        'polymorphic_identity': 'return'
    }

    def process(self):
        self.status = 'processing_return'
        self.date = datetime.utcnow()
        return {
            'message': 'Return initiated',
            'details': {
                'reason': self.reason,
                'refund_amount': self.refund_amount
            }
        } 