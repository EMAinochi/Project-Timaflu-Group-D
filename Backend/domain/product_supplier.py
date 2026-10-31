from dataclasses import dataclass

from domain.manufacturer import Manufacturer
from domain.product import Product


@dataclass
class ProductSupplier:
    product: Product
    manufacturer: Manufacturer
    purchase_price: float
