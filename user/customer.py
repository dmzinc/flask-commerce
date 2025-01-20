from user.user import User
from db import db

class Customer(User):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'customer'
    }