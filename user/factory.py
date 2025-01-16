from user.customer import Customer
from user.admin import Administrator

class UserFactory:
    @staticmethod
    def create_user(user_type, **kwargs):
        if user_type == "customer":
            return Customer(**kwargs)
        elif user_type == "administrator":
            return Administrator(**kwargs)
        else:
            raise ValueError(f"Invalid user type: {user_type}") 