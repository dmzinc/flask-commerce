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

    __mapper_args__ = {
        'polymorphic_identity': 'order',
        'polymorphic_on': type
    }

    @abstractmethod
    def process(self):
        pass

    def __repr__(self):
        return f'<Order {self.id}>' 