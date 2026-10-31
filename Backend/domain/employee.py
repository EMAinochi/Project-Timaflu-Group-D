from dataclasses import dataclass


@dataclass
class Employee:
    employee_id: int
    name: str
    department: str

    def get_name(self) -> str:
        return self.name
