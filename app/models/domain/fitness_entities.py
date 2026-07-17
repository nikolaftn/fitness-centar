from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    role: str
    first_name: str
    last_name: str
    birth_date: str
    password: str
    registration_status: str
    created_at: str

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@dataclass
class TrainerProfile:
    user: User
    education: str
    diploma_license: str
    biography: str
    years_of_experience: int
    price_per_training: float

    @property
    def user_id(self):
        return self.user.id

    @property
    def username(self):
        return self.user.username

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def birth_date(self):
        return self.user.birth_date

    @property
    def full_name(self):
        return self.user.full_name


@dataclass
class TrainerClientRelation:
    trainer: User
    client: User
    monthly_price: float
    expiration_date: str
    is_paid: bool
    status: str
    workouts_per_week: int
    goals: str
    height_cm: float
    weight_kg: float
    training_location: str
    health_conditions: str

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def client_id(self):
        return self.client.id

    @property
    def trainer_name(self):
        return self.trainer.full_name

    @property
    def client_name(self):
        return self.client.full_name


@dataclass
class ClientRating:
    trainer: User
    client: User
    rating: int
    comment: str
    created_at: str

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def client_id(self):
        return self.client.id


@dataclass
class TrainerRating:
    client: User
    trainer: User
    rating: int
    comment: str
    created_at: str

    @property
    def client_id(self):
        return self.client.id

    @property
    def trainer_id(self):
        return self.trainer.id


@dataclass
class Equipment:
    id: int
    name: str
    category: str
    description: str


@dataclass
class Exercise:
    trainer: User
    id: int
    name: str
    description: str
    duration_minutes: int
    equipment: Equipment

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def equipment_id(self):
        if self.equipment is None:
            return None
        return self.equipment.id

    @property
    def equipment_name(self):
        if self.equipment is None:
            return None
        return self.equipment.name


@dataclass
class Workout:
    id: int
    relation: TrainerClientRelation
    name: str
    scheduled_date: str
    status: str

    @property
    def trainer(self):
        return self.relation.trainer

    @property
    def client(self):
        return self.relation.client

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def client_id(self):
        return self.client.id


@dataclass
class WorkoutExercise:
    workout: Workout
    exercise: Exercise
    exercise_order: int
    sets: int
    repetitions: int
    duration_minutes: int
    completed: bool
    completed_at: str

    @property
    def workout_id(self):
        return self.workout.id

    @property
    def exercise_id(self):
        return self.exercise.id

    @property
    def id(self):
        return self.exercise.id

    @property
    def name(self):
        return self.exercise.name

    @property
    def description(self):
        return self.exercise.description

    @property
    def equipment(self):
        return self.exercise.equipment

    @property
    def equipment_name(self):
        return self.exercise.equipment_name

    @property
    def shown_duration_minutes(self):
        if self.duration_minutes is not None:
            return self.duration_minutes
        return self.exercise.duration_minutes


@dataclass
class WorkoutRating:
    workout: Workout
    client: User
    rating: int
    comment: str
    created_at: str

    @property
    def workout_id(self):
        return self.workout.id

    @property
    def client_id(self):
        return self.client.id


@dataclass
class ExerciseRating:
    workout_exercise: WorkoutExercise
    client: User
    rating: int
    comment: str
    created_at: str

    @property
    def workout(self):
        return self.workout_exercise.workout

    @property
    def exercise(self):
        return self.workout_exercise.exercise

    @property
    def workout_id(self):
        return self.workout.id

    @property
    def exercise_id(self):
        return self.exercise.id

    @property
    def client_id(self):
        return self.client.id


@dataclass
class Payment:
    id: int
    relation: TrainerClientRelation
    amount: float
    status: str
    paid_at: str
    valid_until: str

    @property
    def trainer(self):
        return self.relation.trainer

    @property
    def client(self):
        return self.relation.client

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def client_id(self):
        return self.client.id


@dataclass
class TrainerCenterPayment:
    id: int
    trainer: User
    amount: float
    status: str
    paid_at: str
    valid_until: str

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def rent_status(self):
        now = datetime.now()
        paid_at = datetime.fromisoformat(self.paid_at)
        valid_until = datetime.fromisoformat(self.valid_until)
        if paid_at <= now < valid_until:
            return "active"
        return "expired"


@dataclass
class Notification:
    id: int
    client: User
    trainer: User
    payment: Payment
    notification_type: str
    message: str
    is_read: bool
    created_at: str

    @property
    def client_id(self):
        return self.client.id

    @property
    def trainer_id(self):
        return self.trainer.id

    @property
    def payment_id(self):
        return self.payment.id


@dataclass
class Message:
    id: int
    sender: User
    receiver: User
    text: str
    message_type: str
    rating_key: str
    created_at: str

    @property
    def sender_id(self):
        return self.sender.id

    @property
    def receiver_id(self):
        return self.receiver.id

    @property
    def sender_username(self):
        return self.sender.username
