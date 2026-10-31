from dataclasses import dataclass
from datetime import date

from domain.manufacturer import Manufacturer
from domain.product import Product


@dataclass
class PurchaseOrder:
    purchase_id: int
    order_date: date
    product: Product
    manufacturer: Manufacturer
    quantity: int
    price: float
