from orders.purchase import Purchase
from orders.return_order import Return
from orders.exchange import Exchange

class OrderFactory:
    @staticmethod
    def create_order(order_type, **kwargs):
        if order_type == "purchase":
            return Purchase(**kwargs)
        elif order_type == "return":
            return Return(**kwargs)
        elif order_type == "exchange":
            return Exchange(**kwargs)
        else:
            raise ValueError(f"Invalid order type: {order_type}") 