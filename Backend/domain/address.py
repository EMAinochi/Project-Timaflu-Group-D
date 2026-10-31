from dataclasses import dataclass


@dataclass
class Address:
    street: str
    postal_code: str
    city: str

    def formatted(self) -> str:
        return f"{self.street}, {self.postal_code} {self.city}"
