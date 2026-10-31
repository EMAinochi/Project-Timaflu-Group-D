from dataclasses import dataclass

from domain.product import Product


@dataclass
class OrderLine:
    product: Product
    quantity: int
    price: float
    delivered_quantity: int = 0
    backorder: bool = False
