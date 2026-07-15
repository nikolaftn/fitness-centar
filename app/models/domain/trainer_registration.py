from dataclasses import dataclass


@dataclass(frozen=True)
class TrainerRegistration:
    """Zahtev trenera koji administrator pregledava."""

    user_id: int
    username: str
    first_name: str
    last_name: str
    education: str
    years_of_experience: int
    price_per_training: float

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

