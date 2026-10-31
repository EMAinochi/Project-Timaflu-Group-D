from dataclasses import dataclass, field
from datetime import date

from domain.customer import Customer
from domain.order import Order


@dataclass
class Invoice:
    invoice_id: int
    customer: Customer
    invoice_date: date
    orders: list[Order] = field(default_factory=list)
    vat_rate: float = 0.09
    paid: bool = False
    reminder_count: int = 0
    payment_plan: bool = False
    collection_agency: bool = False

    def calculate_vat(self, amount_ex_vat: float) -> float:
        return round(amount_ex_vat * self.vat_rate, 2)

    def calculate_total(self) -> float:
        return sum(order.calculate_total() for order in self.orders)

    def mark_paid(self) -> None:
        self.paid = True
