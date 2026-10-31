from dataclasses import dataclass


@dataclass
class Product:
    product_id: str
    order_code: str
    name: str
    stock: int = 0
    minimum_stock: int = 0
    warehouse_location: str = ""
    price: float = 0.0

    def reduce_stock(self, quantity: int) -> None:
        self.stock = max(0, self.stock - quantity)

    def is_below_minimum_stock(self) -> bool:
        return self.stock < self.minimum_stock
