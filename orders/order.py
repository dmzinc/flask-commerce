from abc import ABC, abstractmethod
from db import db
from sqlalchemy.ext.declarative import DeclarativeMeta
from abc import ABCMeta
from datetime import datetime

class OrderMeta(DeclarativeMeta, ABCMeta):
    pass

class Order(db.Model):
    __metaclass__ = OrderMeta
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50))
    type = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float)

    __mapper_args__ = {
        'polymorphic_identity': 'order',
        'polymorphic_on': type
    }

    @abstractmethod
    def process(self):
        pass

    def get_details(self):
        base_details = {
            'order_id': self.id,
            'product_id': self.product_id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'type': self.type,
            'quantity': self.quantity,
            'total_price': self.total_price
        }
        
        if hasattr(self, 'process'):
            additional_details = self.process()['details']
            base_details.update(additional_details)
        
        return base_details 