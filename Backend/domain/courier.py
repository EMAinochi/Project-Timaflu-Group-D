from dataclasses import dataclass
from datetime import date

from domain.employee import Employee


@dataclass
class Courier(Employee):
    region: str = ""
    phone_number: str = ""
    available: bool = True
    external: bool = False

    def mark_available(self, available: bool = True) -> None:
        self.available = available

    def get_trip(self, trip_date: date) -> list:
        """Return scheduled deliveries for a date (implemented in repository layer)."""
        return []
