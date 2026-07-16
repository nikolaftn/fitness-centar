from datetime import date

from app.models.services.validation import (
    parse_client_request,
    parse_rating,
    validate_profile_data,
)


class FitnessService:
    """Poslovna pravila za rad klijenta i trenera."""

    def __init__(self, fitness_repository, user_repository):
        self.fitness_repository = fitness_repository
        self.user_repository = user_repository

    def get_client_dashboard_data(self, client_id):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.mark_overdue_workouts()
        return {
            "trainers": self.fitness_repository.list_available_trainers(client_id),
            "relations": self.fitness_repository.list_client_relations(client_id),
        }

    def get_trainer_dashboard_data(self, trainer_id):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.mark_overdue_workouts()
        return {
            "requests": self.fitness_repository.list_trainer_requests(trainer_id),
            "clients": self.fitness_repository.list_accepted_clients(trainer_id),
        }

    def get_trainer_profile(self, trainer_id):
        return self.fitness_repository.get_trainer_profile(trainer_id)

    def get_exercises(self):
        return self.fitness_repository.list_exercises()

    def get_equipment(self):
        return self.fitness_repository.list_equipment()

    def get_client_ratings(self, client_id):
        return self.fitness_repository.list_client_ratings(client_id)

    def send_client_request(self, trainer_id, client_id, data):
        request = parse_client_request(data)
        price_per_training = self.fitness_repository.get_trainer_price(trainer_id)
        if price_per_training is None:
            raise ValueError("Izabrani trener nema profil.")
        monthly_price = price_per_training * request["workouts_per_week"] * 4
        self.fitness_repository.create_client_request(
            trainer_id, client_id, **request, monthly_price=monthly_price
        )

    def get_client_workouts(self, client_id, trainer_id):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.mark_overdue_workouts()
        if self.fitness_repository.get_active_membership_expiration(
            trainer_id, client_id
        ) is None:
            raise ValueError("Treninzi se mogu otvoriti samo tokom aktivne clanarine.")
        return self.fitness_repository.list_client_workouts(client_id, trainer_id)

    def get_workout_exercises(self, workout_id, client_id):
        return self.fitness_repository.list_workout_exercises(workout_id, client_id)

    def rate_workout(self, workout_id, client_id, rating, comment):
        self._validate_client_workout_action(workout_id, client_id)
        if not self.fitness_repository.all_workout_exercises_completed(workout_id):
            raise ValueError("Prvo oznacite sve vezbe iz treninga kao odradjene.")
        self.fitness_repository.rate_workout(
            workout_id, client_id, parse_rating(rating), comment.strip()
        )

    def rate_trainer(self, trainer_id, client_id, rating, comment):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.rate_trainer(
            trainer_id, client_id, parse_rating(rating), comment.strip()
        )

    def rate_exercise(self, workout_id, exercise_id, client_id, rating, comment):
        self._validate_client_workout_action(workout_id, client_id)
        if not self.fitness_repository.is_workout_exercise_completed(
            workout_id, exercise_id
        ):
            raise ValueError("Vezbu mozete oceniti tek kada je oznacite kao odradjenu.")
        self.fitness_repository.rate_exercise(
            workout_id, exercise_id, client_id, parse_rating(rating), comment.strip()
        )

    def set_exercise_completed(
        self, workout_id, exercise_id, client_id, completed
    ):
        workout = self._validate_client_workout_action(workout_id, client_id)
        if workout["status"] != "assigned":
            raise ValueError("Zavrsen trening vise ne mozete menjati.")
        self.fitness_repository.set_workout_exercise_completed(
            workout_id, exercise_id, client_id, completed
        )

    def pay_membership(self, trainer_id, client_id):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.pay_monthly_subscription(trainer_id, client_id)

    def get_unread_notifications(self, client_id):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.create_membership_notifications(client_id)
        return self.fitness_repository.list_unread_notifications(client_id)

    def mark_notification_read(self, notification_id, client_id):
        self.fitness_repository.mark_notification_read(notification_id, client_id)

    def update_client_profile(self, user_id, data):
        error = validate_profile_data(data)
        if error:
            raise ValueError(error)
        return self.user_repository.update_profile(
            user_id, data["first_name"].strip(), data["last_name"].strip(),
            data["birth_date"].strip(),
        )

    def save_trainer_profile(self, trainer_id, data):
        error = validate_profile_data(data)
        if error:
            raise ValueError(error)
        try:
            years = int(data["years_of_experience"])
            price = float(data["price_per_training"].replace(",", "."))
        except ValueError as error:
            raise ValueError("Iskustvo i cena moraju biti nenegativni brojevi.") from error
        if years < 0 or price < 0:
            raise ValueError("Iskustvo i cena moraju biti nenegativni brojevi.")
        data = data.copy()
        data["years_of_experience"] = years
        data["price_per_training"] = price
        self.fitness_repository.update_trainer_profile(trainer_id, data)

    def decide_client_request(self, trainer_id, client_id, status):
        if status not in {"accepted", "rejected"}:
            raise ValueError("Neispravan status.")
        return self.fitness_repository.decide_client_request(
            trainer_id, client_id, status
        )

    def save_exercise(self, data):
        if not data["name"]:
            raise ValueError("Naziv vezbe je obavezan.")
        try:
            duration = int(data["duration_minutes"]) if data["duration_minutes"] else None
        except ValueError as error:
            raise ValueError("Trajanje mora biti pozitivan ceo broj.") from error
        if duration is not None and duration <= 0:
            raise ValueError("Trajanje mora biti pozitivan ceo broj.")
        self.fitness_repository.save_exercise(
            data["id"], data["name"], data["description"], duration,
            data["equipment_id"],
        )

    def delete_exercise(self, exercise_id):
        self.fitness_repository.delete_exercise(exercise_id)

    def save_equipment(self, data):
        if not data["name"]:
            raise ValueError("Naziv opreme je obavezan.")
        if data["category"] not in {"machine", "prop"}:
            raise ValueError("Kategorija mora biti machine ili prop.")
        self.fitness_repository.save_equipment(
            data["id"], data["name"], data["category"], data["description"]
        )

    def delete_equipment(self, equipment_id):
        self.fitness_repository.delete_equipment(equipment_id)

    def create_workout(self, trainer_id, client_id, name, exercise_ids, scheduled_date):
        if not name:
            raise ValueError("Naziv treninga je obavezan.")
        if not exercise_ids:
            raise ValueError("Izaberite bar jednu vezbu.")
        deadline = self._validate_workout_deadline(scheduled_date)
        self._validate_workout_assignment(trainer_id, client_id, deadline)
        self.fitness_repository.create_workout(
            trainer_id, client_id, name, exercise_ids, scheduled_date
        )

    @staticmethod
    def _validate_workout_deadline(scheduled_date):
        if not scheduled_date:
            raise ValueError("Rok za zavrsetak treninga je obavezan.")
        try:
            deadline = date.fromisoformat(scheduled_date)
        except ValueError as error:
            raise ValueError("Rok mora biti datum u formatu GGGG-MM-DD.") from error
        if deadline < date.today():
            raise ValueError("Rok za trening ne moze biti u proslosti.")
        return deadline

    def _validate_workout_assignment(self, trainer_id, client_id, deadline):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.mark_overdue_workouts()
        expiration = self.fitness_repository.get_active_membership_expiration(
            trainer_id, client_id
        )
        if expiration is None:
            raise ValueError(
                "Klijent nema aktivnu mesecnu clanarinu kod ovog trenera."
            )
        membership_deadline = date.fromisoformat(expiration[:10])
        if deadline >= membership_deadline:
            raise ValueError(
                "Rok treninga mora biti pre isteka clanarine "
                f"({membership_deadline.isoformat()})."
            )
        missed_count = (
            self.fitness_repository.count_missed_workouts_in_active_membership(
                trainer_id, client_id
            )
        )
        if missed_count >= 2:
            raise ValueError(
                "Klijent je u ovoj clanarini propustio dva treninga. "
                "Novi trening moze dobiti tek posle sledece mesecne uplate."
            )

    def _validate_client_workout_action(self, workout_id, client_id):
        self.fitness_repository.sync_membership_statuses()
        self.fitness_repository.mark_overdue_workouts()
        workout = self.fitness_repository.get_client_workout(workout_id, client_id)
        if workout is None:
            raise ValueError("Trening nije pronadjen.")
        if workout["status"] == "missed":
            raise ValueError("Rok za ovaj trening je istekao.")
        if date.fromisoformat(workout["scheduled_date"]) < date.today():
            raise ValueError("Rok za ovaj trening je istekao.")
        if self.fitness_repository.get_active_membership_expiration(
            workout["trainer_id"], client_id
        ) is None:
            raise ValueError("Clanarina kod ovog trenera vise nije aktivna.")
        return workout

    def save_client_rating(self, trainer_id, client_id, rating, comment):
        self.fitness_repository.save_client_rating(
            trainer_id, client_id, parse_rating(rating), comment.strip()
        )

    def get_messages(self, first_user_id, second_user_id):
        return self.fitness_repository.list_messages(first_user_id, second_user_id)

    def send_message(self, sender_id, receiver_id, text):
        text = text.strip()
        if not text:
            raise ValueError("Poruka ne moze biti prazna.")
        self.fitness_repository.send_message(sender_id, receiver_id, text)

    def get_admin_id(self):
        admin_id = self.fitness_repository.get_admin_id()
        if admin_id is None:
            raise ValueError("Administrator nije pronadjen.")
        return admin_id
