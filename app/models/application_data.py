from app.database import get_connection
from app.models.domain.fitness_entities import (
    ClientRating,
    Equipment,
    Exercise,
    ExerciseRating,
    Message,
    Notification,
    Payment,
    TrainerCenterPayment,
    TrainerClientRelation,
    TrainerProfile,
    TrainerRating,
    User,
    Workout,
    WorkoutExercise,
    WorkoutRating,
)


class ApplicationData:
    """Svi objekti koje aplikacija drzi u memoriji tokom rada."""

    def __init__(self, connection_factory=get_connection):
        self.connection_factory = connection_factory
        self.clear()

    def clear(self):
        self.users = {}
        self.trainer_profiles = {}
        self.trainer_client_relations = {}
        self.client_ratings = {}
        self.trainer_ratings = {}
        self.equipment = {}
        self.exercises = {}
        self.workouts = {}
        self.workout_exercises = {}
        self.workout_ratings = {}
        self.exercise_ratings = {}
        self.payments = {}
        self.trainer_center_payments = {}
        self.notifications = {}
        self.messages = {}

    def load_all(self):
        """Ucita sve tabele i odmah poveze strane kljuceve sa objektima."""
        connection = self.connection_factory()
        try:
            self.clear()
            self._load_users(connection)
            self._load_trainer_profiles(connection)
            self._load_relations(connection)
            self._load_client_ratings(connection)
            self._load_trainer_ratings(connection)
            self._load_equipment(connection)
            self._load_exercises(connection)
            self._load_workouts(connection)
            self._load_workout_exercises(connection)
            self._load_workout_ratings(connection)
            self._load_exercise_ratings(connection)
            self._load_payments(connection)
            self._load_trainer_center_payments(connection)
            self._load_notifications(connection)
            self._load_messages(connection)
        finally:
            connection.close()

    def _load_users(self, connection):
        rows = connection.execute("SELECT * FROM users ORDER BY id").fetchall()
        for row in rows:
            user = User(
                row["id"],
                row["username"],
                row["role"],
                row["first_name"],
                row["last_name"],
                row["birth_date"],
                row["password"],
                row["registration_status"],
                row["created_at"],
            )
            self.users[user.id] = user

    def _load_trainer_profiles(self, connection):
        rows = connection.execute("SELECT * FROM trainer_profiles").fetchall()
        for row in rows:
            profile = TrainerProfile(
                self.users[row["user_id"]],
                row["education"],
                row["diploma_license"],
                row["biography"],
                row["years_of_experience"],
                row["price_per_training"],
            )
            self.trainer_profiles[profile.user.id] = profile

    def _load_relations(self, connection):
        rows = connection.execute("SELECT * FROM trainer_client_relations").fetchall()
        for row in rows:
            relation = TrainerClientRelation(
                self.users[row["trainer_id"]],
                self.users[row["client_id"]],
                row["monthly_price"],
                row["expiration_date"],
                bool(row["is_paid"]),
                row["status"],
                row["workouts_per_week"],
                row["goals"],
                row["height_cm"],
                row["weight_kg"],
                row["training_location"],
                row["health_conditions"],
            )
            key = (relation.trainer.id, relation.client.id)
            self.trainer_client_relations[key] = relation

    def _load_client_ratings(self, connection):
        rows = connection.execute("SELECT * FROM client_ratings").fetchall()
        for row in rows:
            rating = ClientRating(
                self.users[row["trainer_id"]],
                self.users[row["client_id"]],
                row["rating"],
                row["comment"],
                row["created_at"],
            )
            key = (rating.trainer.id, rating.client.id)
            self.client_ratings[key] = rating

    def _load_trainer_ratings(self, connection):
        rows = connection.execute("SELECT * FROM trainer_ratings").fetchall()
        for row in rows:
            rating = TrainerRating(
                self.users[row["client_id"]],
                self.users[row["trainer_id"]],
                row["rating"],
                row["comment"],
                row["created_at"],
            )
            key = (rating.client.id, rating.trainer.id)
            self.trainer_ratings[key] = rating

    def _load_equipment(self, connection):
        rows = connection.execute("SELECT * FROM equipment ORDER BY id").fetchall()
        for row in rows:
            item = Equipment(
                row["id"], row["name"], row["category"], row["description"]
            )
            self.equipment[item.id] = item

    def _load_exercises(self, connection):
        rows = connection.execute(
            "SELECT * FROM exercises ORDER BY trainer_id, id"
        ).fetchall()
        for row in rows:
            equipment = self.equipment.get(row["equipment_id"])
            exercise = Exercise(
                self.users[row["trainer_id"]],
                row["id"],
                row["name"],
                row["description"],
                row["duration_minutes"],
                equipment,
            )
            key = (exercise.trainer.id, exercise.id)
            self.exercises[key] = exercise

    def _load_workouts(self, connection):
        rows = connection.execute("SELECT * FROM workouts ORDER BY id").fetchall()
        for row in rows:
            relation_key = (row["trainer_id"], row["client_id"])
            workout = Workout(
                row["id"],
                self.trainer_client_relations[relation_key],
                row["name"],
                row["scheduled_date"],
                row["status"],
            )
            self.workouts[workout.id] = workout

    def _load_workout_exercises(self, connection):
        rows = connection.execute("SELECT * FROM workout_exercises").fetchall()
        for row in rows:
            item = WorkoutExercise(
                self.workouts[row["workout_id"]],
                self.exercises[(row["trainer_id"], row["exercise_id"])],
                row["exercise_order"],
                row["sets"],
                row["repetitions"],
                row["duration_minutes"],
                bool(row["completed"]),
                row["completed_at"],
            )
            key = (item.workout.id, item.exercise.id)
            self.workout_exercises[key] = item

    def _load_workout_ratings(self, connection):
        rows = connection.execute("SELECT * FROM workout_ratings").fetchall()
        for row in rows:
            rating = WorkoutRating(
                self.workouts[row["workout_id"]],
                self.users[row["client_id"]],
                row["rating"],
                row["comment"],
                row["created_at"],
            )
            key = (rating.workout.id, rating.client.id)
            self.workout_ratings[key] = rating

    def _load_exercise_ratings(self, connection):
        rows = connection.execute("SELECT * FROM exercise_ratings").fetchall()
        for row in rows:
            workout_exercise_key = (row["workout_id"], row["exercise_id"])
            rating = ExerciseRating(
                self.workout_exercises[workout_exercise_key],
                self.users[row["client_id"]],
                row["rating"],
                row["comment"],
                row["created_at"],
            )
            key = (rating.workout.id, rating.exercise.id, rating.client.id)
            self.exercise_ratings[key] = rating

    def _load_payments(self, connection):
        rows = connection.execute("SELECT * FROM payments ORDER BY id").fetchall()
        for row in rows:
            relation_key = (row["trainer_id"], row["client_id"])
            payment = Payment(
                row["id"],
                self.trainer_client_relations[relation_key],
                row["amount"],
                row["status"],
                row["paid_at"],
                row["valid_until"],
            )
            self.payments[payment.id] = payment

    def _load_trainer_center_payments(self, connection):
        rows = connection.execute("SELECT * FROM trainer_center_payments ORDER BY id").fetchall()
        for row in rows:
            payment = TrainerCenterPayment(
                row["id"],
                self.users[row["trainer_id"]],
                row["amount"],
                row["status"],
                row["paid_at"],
                row["valid_until"],
            )
            self.trainer_center_payments[payment.id] = payment

    def _load_notifications(self, connection):
        rows = connection.execute("SELECT * FROM notifications ORDER BY id").fetchall()
        for row in rows:
            notification = Notification(
                row["id"],
                self.users[row["client_id"]],
                self.users[row["trainer_id"]],
                self.payments[row["payment_id"]],
                row["notification_type"],
                row["message"],
                bool(row["is_read"]),
                row["created_at"],
            )
            self.notifications[notification.id] = notification

    def _load_messages(self, connection):
        rows = connection.execute("SELECT * FROM messages ORDER BY id").fetchall()
        for row in rows:
            message = Message(
                row["id"],
                self.users[row["sender_id"]],
                self.users[row["receiver_id"]],
                row["text"],
                row["message_type"],
                row["rating_key"],
                row["created_at"],
            )
            self.messages[message.id] = message
