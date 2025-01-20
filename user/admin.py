from user.user import User
from db import db

class Administrator(User):
    __tablename__ = 'administrators'
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'administrator',
        'inherit_condition': (id == User.id)
    } 