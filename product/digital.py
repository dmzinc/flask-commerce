from product.product import Product
from db import db

class DigitalProduct(Product):
    __tablename__ = 'digital_products'
    id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    file_size = db.Column(db.Float)  # in MB
    download_link = db.Column(db.String(500))

    __mapper_args__ = {
        'polymorphic_identity': 'digital'
    }

    def get_details(self):
        return {
            'file_size': self.file_size,
            'download_link': self.download_link
        } 