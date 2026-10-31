from dataclasses import dataclass, field

from domain.address import Address


@dataclass
class Customer:
    customer_id: int
    company_name: str
    contact_person: str
    phone_number: str
    delivery_address: Address
    invoice_address: Address
    region: str = ""
    annual_turnover: float = 0.0
    one_time_discount: bool = False
    blocked: bool = False
    customer_discount_pct: float = 5.0
    orders: list = field(default_factory=list)

    def get_annual_turnover(self) -> float:
        return self.annual_turnover

    def get_customer_discount(self) -> float:
        return self.customer_discount_pct
