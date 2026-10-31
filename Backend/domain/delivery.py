from dataclasses import dataclass
from datetime import date, time

from domain.courier import Courier
from domain.order import Order


@dataclass
class Delivery:
    delivery_id: int
    order: Order
    courier: Courier | None
    delivery_date: date
    delivery_time: time
    attempts: int = 0
    delivered: bool = False
    signed: bool = False

    def mark_delivered(self, signed: bool = True) -> None:
        self.delivered = True
        self.signed = signed
