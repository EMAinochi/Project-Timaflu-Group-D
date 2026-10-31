from dataclasses import dataclass
from datetime import date

from domain.customer import Customer
from domain.employee import Employee


@dataclass
class Visit:
    visit_id: int
    account_manager: Employee | None
    company_name: str
    contact_person: str
    phone_number: str
    email: str | None
    address: str
    visit_date: date
    follow_up_called: bool = False
    customer: Customer | None = None

    def get_acquisition_overview(self) -> list:
        """Stub — use AcquisitionService.get_overview()."""
        return []
