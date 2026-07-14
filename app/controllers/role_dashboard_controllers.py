from datetime import date

from app.views.role_dashboard_views import ClientDashboardView, TrainerDashboardView


class ClientDashboardController:
    """Kontroler klijentskog CustomTkinter ekrana."""

    def __init__(self, parent, user, fitness_repository, user_repository):
        self.user = user
        self.fitness_repository = fitness_repository
        self.user_repository = user_repository
        self.view = ClientDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        self.view.show_trainers(self.fitness_repository.list_available_trainers())
        self.view.show_relations(self.fitness_repository.list_client_relations(self.user.id))
        self.view.show_workouts(self.fitness_repository.list_client_workouts(self.user.id))
        self.view.show_payments(self.fitness_repository.list_payments_for_client(self.user.id))

    def send_request(self):
        trainer_id = self.view.get_selected_trainer_id()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite trenera.")
            return
        try:
            data = self._parse_request_data(self.view.get_request_data())
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.fitness_repository.create_client_request(
            trainer_id=trainer_id,
            client_id=self.user.id,
            **data,
        )
        self.view.show_info("Zahtev je poslat treneru.")
        self.refresh()

    def load_selected_workout_exercises(self):
        workout_id = self.view.get_selected_workout_id()
        if workout_id is None:
            self.view.show_exercises([])
            return
        exercises = self.fitness_repository.list_workout_exercises(
            workout_id, self.user.id
        )
        self.view.show_exercises(exercises)

    def rate_selected_workout_and_trainer(self):
        workout_id = self.view.get_selected_workout_id()
        trainer_id = self.view.get_selected_workout_trainer_id()
        if workout_id is None or trainer_id is None:
            self.view.show_error("Prvo izaberite trening.")
            return
        try:
            workout_rating = self._parse_rating(self.view.workout_rating_var.get())
            trainer_rating = self._parse_rating(self.view.trainer_rating_var.get())
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.fitness_repository.rate_workout(
            workout_id,
            self.user.id,
            workout_rating,
            self.view.workout_comment_var.get().strip(),
        )
        self.fitness_repository.rate_trainer(
            trainer_id,
            self.user.id,
            trainer_rating,
            self.view.trainer_comment_var.get().strip(),
        )
        self.view.show_info("Ocene su sacuvane.")
        self.refresh()
        self.load_selected_workout_exercises()

    def rate_selected_exercise(self):
        workout_id = self.view.get_selected_workout_id()
        exercise_id = self.view.get_selected_exercise_id()
        if workout_id is None or exercise_id is None:
            self.view.show_error("Prvo izaberite trening i vezbu.")
            return
        try:
            rating = self._parse_rating(self.view.exercise_rating_var.get())
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.fitness_repository.rate_exercise(
            workout_id,
            exercise_id,
            self.user.id,
            rating,
            self.view.exercise_comment_var.get().strip(),
        )
        self.view.show_info("Ocena vezbe je sacuvana.")
        self.load_selected_workout_exercises()

    def submit_selected_exercise_video(self):
        workout_id = self.view.get_selected_workout_id()
        exercise_id = self.view.get_selected_exercise_id()
        video_url = self.view.exercise_video_var.get().strip()
        if workout_id is None or exercise_id is None:
            self.view.show_error("Prvo izaberite trening i vezbu.")
            return
        if not video_url:
            self.view.show_error("Unesite putanju ili link snimka.")
            return
        self.fitness_repository.submit_exercise_video(
            workout_id,
            exercise_id,
            self.user.id,
            video_url,
            self.view.exercise_video_comment_var.get().strip(),
        )
        self.view.show_info("Snimak vezbe je poslat treneru.")
        self.load_selected_workout_exercises()

    def pay_selected_trainer(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        period = self.view.payment_period_var.get().strip()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite prihvacenog trenera.")
            return
        if not period:
            self.view.show_error("Unesite period placanja, npr. 2026-07.")
            return
        try:
            self.fitness_repository.pay_monthly_subscription(
                trainer_id, self.user.id, period
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Mesecna pretplata je evidentirana.")
        self.refresh()

    def load_chat(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        if trainer_id is None:
            self.view.show_messages([])
            return
        messages = self.fitness_repository.list_messages(self.user.id, trainer_id)
        self.view.show_messages(messages)

    def send_message(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        text = self.view.message_var.get().strip()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite trenera za chat.")
            return
        if not text:
            self.view.show_error("Poruka ne moze biti prazna.")
            return
        self.fitness_repository.send_message(self.user.id, trainer_id, text)
        self.view.message_var.set("")
        self.load_chat()

    def update_profile(self):
        data = self.view.get_profile_data()
        error = validate_profile_data(data)
        if error:
            self.view.show_error(error)
            return
        self.user = self.user_repository.update_profile(
            self.user.id,
            data["first_name"],
            data["last_name"],
            data["birth_date"],
        )
        self.view.show_info("Profil je azuriran.")

    @staticmethod
    def _parse_request_data(data):
        try:
            workouts_per_week = int(data["workouts_per_week"])
            height_cm = float(data["height_cm"].replace(",", "."))
            weight_kg = float(data["weight_kg"].replace(",", "."))
        except ValueError as error:
            raise ValueError(
                "Broj treninga, visina i tezina moraju biti brojevi."
            ) from error
        if not 1 <= workouts_per_week <= 7:
            raise ValueError("Broj treninga nedeljno mora biti od 1 do 7.")
        if data["training_location"] not in {"gym", "home", "both"}:
            raise ValueError("Lokacija mora biti gym, home ili both.")
        return {
            "workouts_per_week": workouts_per_week,
            "goals": data["goals"],
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "training_location": data["training_location"],
            "health_conditions": data["health_conditions"],
        }

    @staticmethod
    def _parse_rating(value):
        try:
            rating = int(value)
        except ValueError as error:
            raise ValueError("Ocena mora biti ceo broj od 1 do 5.") from error
        if not 1 <= rating <= 5:
            raise ValueError("Ocena mora biti od 1 do 5.")
        return rating


class TrainerDashboardController:
    """Minimalan trenerski kontroler potreban za klijent funkcionalnosti."""

    def __init__(self, parent, user, fitness_repository):
        self.user = user
        self.fitness_repository = fitness_repository
        self.view = TrainerDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        self.view.show_requests(self.fitness_repository.list_trainer_requests(self.user.id))
        self.view.show_clients(self.fitness_repository.list_accepted_clients(self.user.id))
        self.view.show_exercises(self.fitness_repository.list_exercises())

    def accept_selected_request(self):
        self._decide_selected_request("accepted")

    def reject_selected_request(self):
        self._decide_selected_request("rejected")

    def _decide_selected_request(self, status):
        client_id = self.view.get_selected_request_client_id()
        if client_id is None:
            self.view.show_error("Prvo izaberite zahtev klijenta.")
            return
        changed = self.fitness_repository.decide_client_request(
            self.user.id, client_id, status
        )
        if not changed:
            self.view.show_error("Zahtev vise nije na cekanju.")
            return
        message = "prihvacen" if status == "accepted" else "odbijen"
        self.view.show_info(f"Zahtev je {message}.")
        self.refresh()

    def create_exercise(self):
        name = self.view.exercise_name_var.get().strip()
        description = self.view.exercise_description_var.get().strip()
        video_url = self.view.exercise_tutorial_var.get().strip()
        if not name:
            self.view.show_error("Unesite naziv vezbe.")
            return
        self.fitness_repository.create_exercise(name, description, video_url)
        self.view.exercise_name_var.set("")
        self.view.exercise_description_var.set("")
        self.view.exercise_tutorial_var.set("")
        self.view.show_info("Vezba je sacuvana.")
        self.refresh()

    def create_workout(self):
        client_id = self.view.get_selected_client_id()
        exercise_ids = self.view.get_selected_exercise_ids()
        program_name = self.view.program_name_var.get().strip()
        workout_name = self.view.workout_name_var.get().strip()
        scheduled_date = self.view.scheduled_date_var.get().strip()
        if client_id is None:
            self.view.show_error("Prvo izaberite klijenta.")
            return
        if not program_name or not workout_name:
            self.view.show_error("Unesite naziv programa i treninga.")
            return
        if not exercise_ids:
            self.view.show_error("Izaberite bar jednu vezbu.")
            return
        self.fitness_repository.create_program_with_workout(
            self.user.id,
            client_id,
            program_name,
            workout_name,
            exercise_ids,
            scheduled_date,
        )
        self.view.show_info("Trening je kreiran za klijenta.")


def validate_profile_data(data):
    if not data["first_name"] or not data["last_name"] or not data["birth_date"]:
        return "Ime, prezime i datum rodjenja su obavezni."
    try:
        birth_date = date.fromisoformat(data["birth_date"])
    except ValueError:
        return "Datum rodjenja mora biti u formatu GGGG-MM-DD."
    if birth_date > date.today():
        return "Datum rodjenja ne moze biti u buducnosti."
    return None
