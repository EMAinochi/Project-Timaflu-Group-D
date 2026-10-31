from dataclasses import dataclass

from domain.purchase_order import PurchaseOrder


@dataclass
class PurchaseInvoice:
    invoice_number: int
    purchase_order: PurchaseOrder
    amount: float
    paid: bool = False

    def mark_paid(self) -> None:
        self.paid = True
