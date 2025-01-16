from product.product import Product
from db import db

class PhysicalProduct(Product):
    __tablename__ = 'physical_products'
    id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    weight = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
    
    __mapper_args__ = {
        'polymorphic_identity': 'physical'
    }

    def get_details(self):
        return {
            'weight': self.weight,
            'stock': self.stock
        } 