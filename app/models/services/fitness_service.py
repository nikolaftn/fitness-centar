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
        return {
            "trainers": self.fitness_repository.list_available_trainers(),
            "relations": self.fitness_repository.list_client_relations(client_id),
            "workouts": self.fitness_repository.list_client_workouts(client_id),
            "payments": self.fitness_repository.list_payments_for_client(client_id),
        }

    def get_trainer_dashboard_data(self, trainer_id):
        return {
            "profile": self.fitness_repository.get_trainer_profile(trainer_id),
            "requests": self.fitness_repository.list_trainer_requests(trainer_id),
            "clients": self.fitness_repository.list_accepted_clients(trainer_id),
            "exercises": self.fitness_repository.list_exercises(),
            "equipment": self.fitness_repository.list_equipment(),
            "workouts": self.fitness_repository.list_trainer_workouts(trainer_id),
            "client_ratings": self.fitness_repository.list_client_ratings_for_trainers(),
        }

    def send_client_request(self, trainer_id, client_id, data):
        request = parse_client_request(data)
        price_per_training = self.fitness_repository.get_trainer_price(trainer_id)
        if price_per_training is None:
            raise ValueError("Izabrani trener nema profil.")
        monthly_price = price_per_training * request["workouts_per_week"] * 4
        self.fitness_repository.create_client_request(
            trainer_id, client_id, **request, monthly_price=monthly_price
        )

    def get_workout_exercises(self, workout_id, client_id):
        return self.fitness_repository.list_workout_exercises(workout_id, client_id)

    def rate_workout(self, workout_id, client_id, rating, comment):
        self.fitness_repository.rate_workout(
            workout_id, client_id, parse_rating(rating), comment.strip()
        )

    def rate_trainer(self, trainer_id, client_id, rating, comment):
        self.fitness_repository.rate_trainer(
            trainer_id, client_id, parse_rating(rating), comment.strip()
        )

    def rate_exercise(self, workout_id, exercise_id, client_id, rating, comment):
        self.fitness_repository.rate_exercise(
            workout_id, exercise_id, client_id, parse_rating(rating), comment.strip()
        )

    def pay_membership(self, trainer_id, client_id):
        self.fitness_repository.pay_monthly_subscription(trainer_id, client_id)

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
            data["id"], data["name"], data["description"], data["video_url"],
            duration, data["equipment_id"],
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
        self.fitness_repository.create_workout(
            trainer_id, client_id, name, exercise_ids, scheduled_date
        )

    def copy_workout(self, trainer_id, workout_id, client_id):
        self.fitness_repository.copy_workout_to_client(
            trainer_id, workout_id, client_id
        )

    def mark_workout_missed(self, trainer_id, workout_id):
        self.fitness_repository.update_workout_status(
            trainer_id, workout_id, "missed"
        )

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
