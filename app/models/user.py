from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """Podaci o prijavljenom korisniku bez osetljivih podataka."""

    id: int
    username: str
    role: str
    first_name: str
    last_name: str
    birth_date: str
    registration_status: str

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
