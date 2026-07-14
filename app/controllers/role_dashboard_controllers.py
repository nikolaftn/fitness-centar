from datetime import date

from app.views.role_dashboard_views import ClientDashboardView, TrainerDashboardView


class ClientDashboardController:
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
            return self.view.show_error("Prvo izaberite trenera.")
        try:
            data = self._parse_request_data(self.view.get_request_data())
            self.fitness_repository.create_client_request(trainer_id, self.user.id, **data)
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Zahtev je poslat treneru.")
        self.refresh()

    def load_selected_workout_exercises(self):
        workout_id = self.view.get_selected_workout_id()
        self.view.show_exercises([] if workout_id is None else
                                 self.fitness_repository.list_workout_exercises(workout_id, self.user.id))

    def rate_selected_workout(self):
        workout_id = self.view.get_selected_workout_id()
        if workout_id is None:
            return self.view.show_error("Prvo izaberite trening.")
        try:
            rating = self._parse_rating(self.view.workout_rating_var.get())
            self.fitness_repository.rate_workout(
                workout_id, self.user.id, rating,
                self.view.workout_comment_var.get().strip())
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Trening je oznacen kao odradjen i ocenjen.")
        self.refresh()

    def rate_selected_trainer(self):
        trainer_id = self.view.get_selected_workout_trainer_id()
        if trainer_id is None:
            return self.view.show_error("Prvo izaberite trening tog trenera.")
        try:
            rating = self._parse_rating(self.view.trainer_rating_var.get())
            self.fitness_repository.rate_trainer(
                trainer_id, self.user.id, rating,
                self.view.trainer_comment_var.get().strip())
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Jednokratna recenzija trenera je sacuvana.")
        self.refresh()

    def rate_selected_workout_and_trainer(self):
        self.rate_selected_workout()

    def rate_selected_exercise(self):
        workout_id = self.view.get_selected_workout_id()
        exercise_id = self.view.get_selected_exercise_id()
        if workout_id is None or exercise_id is None:
            return self.view.show_error("Izaberite trening i vezbu.")
        try:
            rating = self._parse_rating(self.view.exercise_rating_var.get())
            self.fitness_repository.rate_exercise(
                workout_id, exercise_id, self.user.id, rating,
                self.view.exercise_comment_var.get().strip())
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Ocena vezbe je sacuvana.")
        self.load_selected_workout_exercises()

    def submit_selected_exercise_video(self):
        workout_id = self.view.get_selected_workout_id()
        exercise_id = self.view.get_selected_exercise_id()
        video = self.view.exercise_video_var.get().strip()
        if workout_id is None or exercise_id is None:
            return self.view.show_error("Izaberite trening i vezbu.")
        if not video:
            return self.view.show_error("Unesite link ili putanju snimka.")
        self.fitness_repository.submit_exercise_video(
            workout_id, exercise_id, self.user.id, video,
            self.view.exercise_video_comment_var.get().strip())
        self.view.show_info("Snimak je poslat treneru.")
        self.load_selected_workout_exercises()

    def pay_selected_trainer(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        period = self.view.payment_period_var.get().strip()
        if trainer_id is None:
            return self.view.show_error("Izaberite prihvacenog trenera.")
        if not period:
            return self.view.show_error("Unesite period, na primer 2026-07.")
        try:
            self.fitness_repository.pay_monthly_subscription(trainer_id, self.user.id, period)
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Pretplata je placena unapred.")
        self.refresh()

    def load_chat(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        self.view.show_messages([] if trainer_id is None else
                                self.fitness_repository.list_messages(self.user.id, trainer_id))

    def send_message(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        text = self.view.message_var.get().strip()
        if trainer_id is None:
            return self.view.show_error("Izaberite prihvacenog trenera za chat.")
        if not text:
            return self.view.show_error("Poruka ne moze biti prazna.")
        self.fitness_repository.send_message(self.user.id, trainer_id, text)
        self.view.message_var.set("")
        self.load_chat()

    def update_profile(self):
        data = self.view.get_profile_data()
        error = validate_profile_data(data)
        if error:
            return self.view.show_error(error)
        self.user = self.user_repository.update_profile(
            self.user.id, data["first_name"], data["last_name"], data["birth_date"])
        self.view.show_info("Profil je azuriran.")

    @staticmethod
    def _parse_request_data(data):
        try:
            workouts = int(data["workouts_per_week"])
            height = float(data["height_cm"].replace(",", "."))
            weight = float(data["weight_kg"].replace(",", "."))
        except ValueError as error:
            raise ValueError("Broj treninga, visina i tezina moraju biti brojevi.") from error
        if not 1 <= workouts <= 7:
            raise ValueError("Broj treninga mora biti od 1 do 7.")
        if data["training_location"] not in {"gym", "home", "both"}:
            raise ValueError("Lokacija mora biti gym, home ili both.")
        return dict(workouts_per_week=workouts, goals=data["goals"],
                    height_cm=height, weight_kg=weight,
                    training_location=data["training_location"],
                    health_conditions=data["health_conditions"])

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
    def __init__(self, parent, user, fitness_repository):
        self.user = user
        self.fitness_repository = fitness_repository
        self.view = TrainerDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        self.view.show_profile(self.fitness_repository.get_trainer_profile(self.user.id))
        self.view.show_requests(self.fitness_repository.list_trainer_requests(self.user.id))
        self.view.show_clients(self.fitness_repository.list_accepted_clients(self.user.id))
        self.view.show_exercises(self.fitness_repository.list_exercises())
        self.view.show_equipment(self.fitness_repository.list_equipment())
        self.view.show_workouts(self.fitness_repository.list_trainer_workouts(self.user.id))
        self.view.show_submissions(self.fitness_repository.list_exercise_submissions_for_trainer(self.user.id))
        self.view.show_client_ratings(self.fitness_repository.list_client_ratings_for_trainers())

    def save_profile(self):
        data = self.view.get_trainer_profile_data()
        error = validate_profile_data(data)
        if error:
            return self.view.show_error(error)
        try:
            data["years_of_experience"] = int(data["years_of_experience"])
            data["price_per_training"] = float(data["price_per_training"].replace(",", "."))
            if data["years_of_experience"] < 0 or data["price_per_training"] < 0:
                raise ValueError
        except ValueError:
            return self.view.show_error("Iskustvo i cena moraju biti nenegativni brojevi.")
        self.fitness_repository.update_trainer_profile(self.user.id, data)
        self.view.show_info("Profil trenera je sacuvan.")
        self.refresh()

    def accept_selected_request(self):
        self._decide("accepted")

    def reject_selected_request(self):
        self._decide("rejected")

    def _decide(self, status):
        client_id = self.view.get_selected_request_client_id()
        if client_id is None:
            return self.view.show_error("Izaberite zahtev klijenta.")
        if not self.fitness_repository.decide_client_request(self.user.id, client_id, status):
            return self.view.show_error("Zahtev vise nije na cekanju.")
        self.view.show_info("Zahtev je prihvacen." if status == "accepted" else "Zahtev je odbijen.")
        self.refresh()

    def save_exercise(self):
        data = self.view.get_exercise_data()
        if not data["name"]:
            return self.view.show_error("Naziv vezbe je obavezan.")
        try:
            duration = int(data["duration_minutes"]) if data["duration_minutes"] else None
            if duration is not None and duration <= 0:
                raise ValueError
            self.fitness_repository.save_exercise(
                data["id"], data["name"], data["description"], data["video_url"], duration)
        except ValueError:
            return self.view.show_error("Trajanje mora biti pozitivan ceo broj.")
        self.view.clear_exercise_form()
        self.view.show_info("Vezba je sacuvana.")
        self.refresh()

    def create_exercise(self):
        self.save_exercise()

    def delete_exercise(self):
        exercise_id = self.view.get_selected_exercise_id()
        if exercise_id is None:
            return self.view.show_error("Izaberite vezbu.")
        self.fitness_repository.delete_exercise(exercise_id)
        self.view.clear_exercise_form()
        self.refresh()

    def save_equipment(self):
        data = self.view.get_equipment_data()
        if not data["name"]:
            return self.view.show_error("Naziv opreme je obavezan.")
        if data["category"] not in {"machine", "prop"}:
            return self.view.show_error("Kategorija mora biti machine ili prop.")
        self.fitness_repository.save_equipment(
            data["id"], data["name"], data["category"], data["description"])
        self.view.clear_equipment_form()
        self.view.show_info("Oprema je sacuvana.")
        self.refresh()

    def delete_equipment(self):
        equipment_id = self.view.get_selected_equipment_id()
        if equipment_id is None:
            return self.view.show_error("Izaberite opremu.")
        self.fitness_repository.delete_equipment(equipment_id)
        self.view.clear_equipment_form()
        self.refresh()

    def create_workout(self):
        client_id = self.view.get_selected_client_id()
        exercise_ids = self.view.get_selected_exercise_ids()
        if client_id is None:
            return self.view.show_error("Izaberite klijenta.")
        if not exercise_ids:
            return self.view.show_error("Izaberite bar jednu vezbu.")
        if not self.view.program_name_var.get().strip() or not self.view.workout_name_var.get().strip():
            return self.view.show_error("Naziv programa i treninga su obavezni.")
        try:
            self.fitness_repository.create_program_with_workout(
                self.user.id, client_id, self.view.program_name_var.get().strip(),
                self.view.workout_name_var.get().strip(), exercise_ids,
                self.view.scheduled_date_var.get().strip(),
                self.view.program_description_var.get().strip())
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Program i trening su dodeljeni klijentu.")
        self.refresh()

    def copy_selected_program(self):
        workout = self.view.get_selected_trainer_workout()
        client_id = self.view.get_selected_client_id()
        if workout is None or client_id is None:
            return self.view.show_error("Izaberite postojeci trening/program i ciljnog klijenta.")
        try:
            self.fitness_repository.copy_program_to_client(
                self.user.id, workout["program_id"], client_id)
        except ValueError as error:
            return self.view.show_error(str(error))
        self.view.show_info("Program je kopiran drugom klijentu.")
        self.refresh()

    def mark_workout_missed(self):
        workout_id = self.view.get_selected_trainer_workout_id()
        if workout_id is None:
            return self.view.show_error("Izaberite trening.")
        self.fitness_repository.update_workout_status(self.user.id, workout_id, "missed")
        self.view.show_info("Trening je oznacen kao neodradjen.")
        self.refresh()

    def save_client_rating(self):
        client_id = self.view.get_selected_client_id()
        if client_id is None:
            return self.view.show_error("Izaberite klijenta.")
        try:
            rating = ClientDashboardController._parse_rating(self.view.client_rating_var.get())
        except ValueError as error:
            return self.view.show_error(str(error))
        self.fitness_repository.save_client_rating(
            self.user.id, client_id, rating,
            self.view.client_rating_comment_var.get().strip())
        self.view.show_info("Interna ocena klijenta je sacuvana i klijent je ne vidi.")
        self.refresh()

    def load_chat(self):
        client_id = self.view.get_selected_client_id()
        self.view.show_messages([] if client_id is None else
                                self.fitness_repository.list_messages(self.user.id, client_id))

    def send_message(self):
        client_id = self.view.get_selected_client_id()
        text = self.view.message_var.get().strip()
        if client_id is None:
            return self.view.show_error("Izaberite klijenta za chat.")
        if not text:
            return self.view.show_error("Poruka ne moze biti prazna.")
        self.fitness_repository.send_message(self.user.id, client_id, text)
        self.view.message_var.set("")
        self.load_chat()


def validate_profile_data(data):
    if not data["first_name"] or not data["last_name"] or not data["birth_date"]:
        return "Ime, prezime i datum rodjenja su obavezni."
    try:
        parsed = date.fromisoformat(data["birth_date"])
    except ValueError:
        return "Datum rodjenja mora biti GGGG-MM-DD."
    if parsed > date.today():
        return "Datum rodjenja ne moze biti u buducnosti."
    return None
