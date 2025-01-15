import json


class User:
    def __init__(self, name, id = '', email=''):
        self.name = name
        self.id = id
        self.email = email

    def to_dict(self):
        return {"name": self.name, 'id': self.id, 'email': self.email}
    
    def __str__(self):
        return json.dumps(self.to_dict())
    
    @staticmethod
    def populate(cls, *args, ** kwargs):
        cls(*args, **kwargs)
    