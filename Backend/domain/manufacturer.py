from dataclasses import dataclass

from domain.address import Address


@dataclass
class Manufacturer:
    manufacturer_id: int
    name: str
    address: Address
    contact_person: str
    phone_number: str
    website: str | None = None
