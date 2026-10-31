from dataclasses import dataclass, field
from datetime import date

from domain.customer import Customer
from domain.enums import DayPart, OrderStatus
from domain.order_line import OrderLine


@dataclass
class Order:
    order_id: int
    customer: Customer
    order_date: date
    delivery_date: date
    day_part: DayPart | None = None
    urgent: bool = False
    extra_charges: float = 0.0
    charge_note: str = ""
    status: OrderStatus = OrderStatus.BEING_PICKED
    order_lines: list[OrderLine] = field(default_factory=list)

    def calculate_total(self) -> float:
        return sum(line.quantity * line.price for line in self.order_lines)

    def set_status(self, status: OrderStatus) -> None:
        self.status = status
