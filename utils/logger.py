import logging
from functools import wraps
from datetime import datetime
import os


os.makedirs('logs', exist_ok=True)

logging.basicConfig(level=logging.INFO)


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger('ecommerce')
general_handler = logging.FileHandler('logs/general.log')
general_handler.setFormatter(formatter)
logger.addHandler(general_handler)

# User operations logger
user_logger = logging.getLogger('user_operations')
user_handler = logging.FileHandler('logs/user_operations.log')
user_handler.setFormatter(formatter)
user_logger.addHandler(user_handler)

# Product operations logger
product_logger = logging.getLogger('product_operations')
product_handler = logging.FileHandler('logs/product_operations.log')
product_handler.setFormatter(formatter)
product_logger.addHandler(product_handler)

# Cart operations logger
cart_logger = logging.getLogger('cart_operations')
cart_handler = logging.FileHandler('logs/cart_operations.log')
cart_handler.setFormatter(formatter)
cart_logger.addHandler(cart_handler)

# Order operations logger
order_logger = logging.getLogger('order_operations')
order_handler = logging.FileHandler('logs/order_operations.log')
order_handler.setFormatter(formatter)
order_logger.addHandler(order_handler)

# Export all loggers
__all__ = ['logger', 'user_logger', 'product_logger', 'cart_logger', 'order_logger']

def log_user_operation(operation_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                user_logger.info(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Success - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                return result
            except Exception as e:
                user_logger.error(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Failed - "
                    f"Error: {str(e)} - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                raise
        return wrapper
    return decorator

def log_product_operation(operation_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                product_logger.info(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Success - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                return result
            except Exception as e:
                product_logger.error(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Failed - "
                    f"Error: {str(e)} - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                raise
        return wrapper
    return decorator

def log_cart_operation(operation_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                cart_logger.info(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Success - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                return result
            except Exception as e:
                cart_logger.error(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Failed - "
                    f"Error: {str(e)} - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                raise
        return wrapper
    return decorator

def log_order_operation(operation_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                order_logger.info(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Success - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                return result
            except Exception as e:
                order_logger.error(
                    f"Operation: {operation_type} - "
                    f"Function: {func.__name__} - "
                    f"Status: Failed - "
                    f"Error: {str(e)} - "
                    f"Duration: {(datetime.utcnow() - start_time).total_seconds()}s"
                )
                raise
        return wrapper
    return decorator 