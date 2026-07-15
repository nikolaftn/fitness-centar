from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    id: int
    name: str
    description: str | None
    video_url: str | None
    duration_minutes: int | None
    equipment_id: int | None = None
    equipment_name: str | None = None
    exercise_order: int | None = None
    rating: int | None = None
    comment: str | None = None


@dataclass(frozen=True)
class Equipment:
    id: int
    name: str
    category: str
    description: str | None


@dataclass(frozen=True)
class Workout:
    id: int
    name: str
    scheduled_date: str | None
    status: str
    trainer_id: int | None = None
    client_id: int | None = None
    trainer_name: str | None = None
    client_name: str | None = None
    workout_rating: int | None = None
    trainer_rating: int | None = None


@dataclass(frozen=True)
class Payment:
    id: int
    trainer_id: int
    client_id: int
    amount: float
    status: str
    paid_at: str
    valid_until: str
    trainer_name: str | None = None


@dataclass(frozen=True)
class TrainerClientRelation:
    trainer_id: int
    client_id: int
    status: str
    monthly_price: float | None
    expiration_date: str | None
    workouts_per_week: int
    goals: str | None
    height_cm: float | None
    weight_kg: float | None
    training_location: str | None
    health_conditions: str | None
    trainer_name: str | None = None
    client_name: str | None = None

