from product.physical import PhysicalProduct
from product.digital import DigitalProduct

class ProductFactory:
    @staticmethod
    def create_product(product_type, **kwargs):
        if product_type == "physical":
            return PhysicalProduct(**kwargs)
        elif product_type == "digital":
            return DigitalProduct(**kwargs)
        else:
            raise ValueError(f"Invalid product type: {product_type}") 