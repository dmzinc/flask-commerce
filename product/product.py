from abc import ABC, abstractmethod
from db import db
from sqlalchemy.ext.declarative import DeclarativeMeta
from abc import ABCMeta

# Create a custom metaclass that combines both ABCMeta and DeclarativeMeta
class ProductMeta(DeclarativeMeta, ABCMeta):
    pass

# Use the custom metaclass
class Product(db.Model):
    __metaclass__ = ProductMeta
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'product',
        'polymorphic_on': type
    }

    @abstractmethod
    def get_details(self):
        pass

    def __repr__(self):
        return f'<Product {self.name}>' 