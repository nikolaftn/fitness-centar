from app.views.role_dashboard_views import ClientDashboardView, TrainerDashboardView


class ClientDashboardController:
    def __init__(self, parent, user, fitness_service):
        self.user = user
        self.fitness_service = fitness_service
        self.view = ClientDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        data = self.fitness_service.get_client_dashboard_data(self.user.id)
        self.view.show_trainers(data["trainers"])
        self.view.show_relations(data["relations"])
        self.view.show_workouts(data["workouts"])
        self.view.show_payments(data["payments"])

    def send_request(self):
        trainer_id = self.view.get_selected_trainer_id()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite trenera.")
            return
        try:
            self.fitness_service.send_client_request(
                trainer_id, self.user.id, self.view.get_request_data()
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Zahtev je poslat treneru.")
        self.refresh()

    def load_selected_workout_exercises(self):
        workout_id = self.view.get_selected_workout_id()
        rows = [] if workout_id is None else self.fitness_service.get_workout_exercises(
            workout_id, self.user.id
        )
        self.view.show_exercises(rows)

    def rate_selected_workout(self):
        workout_id = self.view.get_selected_workout_id()
        if workout_id is None:
            self.view.show_error("Prvo izaberite trening.")
            return
        try:
            self.fitness_service.rate_workout(
                workout_id, self.user.id, self.view.workout_rating_var.get(),
                self.view.workout_comment_var.get(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Trening je oznacen kao odradjen i ocenjen.")
        self.refresh()

    def rate_selected_trainer(self):
        trainer_id = self.view.get_selected_workout_trainer_id()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite trening tog trenera.")
            return
        try:
            self.fitness_service.rate_trainer(
                trainer_id, self.user.id, self.view.trainer_rating_var.get(),
                self.view.trainer_comment_var.get(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Jednokratna recenzija trenera je sacuvana.")
        self.refresh()

    def rate_selected_exercise(self):
        workout_id = self.view.get_selected_workout_id()
        exercise_id = self.view.get_selected_exercise_id()
        if workout_id is None or exercise_id is None:
            self.view.show_error("Izaberite trening i vezbu.")
            return
        try:
            self.fitness_service.rate_exercise(
                workout_id, exercise_id, self.user.id,
                self.view.exercise_rating_var.get(),
                self.view.exercise_comment_var.get(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Ocena vezbe je sacuvana.")
        self.load_selected_workout_exercises()

    def pay_selected_trainer(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        if trainer_id is None:
            self.view.show_error("Izaberite prihvacenog trenera.")
            return
        try:
            self.fitness_service.pay_membership(trainer_id, self.user.id)
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Clanarina vazi narednih mesec dana.")
        self.refresh()

    def load_chat(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        rows = [] if trainer_id is None else self.fitness_service.get_messages(
            self.user.id, trainer_id
        )
        self.view.show_messages(rows)

    def send_message(self):
        trainer_id = self.view.get_selected_relation_trainer_id()
        if trainer_id is None:
            self.view.show_error("Izaberite prihvacenog trenera za chat.")
            return
        try:
            self.fitness_service.send_message(
                self.user.id, trainer_id, self.view.message_var.get()
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.message_var.set("")
        self.load_chat()
    def update_profile(self):
        try:
            self.user = self.fitness_service.update_client_profile(
                self.user.id, self.view.get_profile_data()
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Profil je azuriran.")


class TrainerDashboardController:
    def __init__(self, parent, user, fitness_service):
        self.user = user
        self.fitness_service = fitness_service
        self.view = TrainerDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        data = self.fitness_service.get_trainer_dashboard_data(self.user.id)
        self.view.show_profile(data["profile"])
        self.view.show_requests(data["requests"])
        self.view.show_clients(data["clients"])
        self.view.show_exercises(data["exercises"])
        self.view.show_equipment(data["equipment"])
        self.view.show_workouts(data["workouts"])
        self.view.show_client_ratings(data["client_ratings"])

    def save_profile(self):
        try:
            self.fitness_service.save_trainer_profile(
                self.user.id, self.view.get_trainer_profile_data()
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Profil trenera je sacuvan.")
        self.refresh()

    def accept_selected_request(self):
        self._decide("accepted")

    def reject_selected_request(self):
        self._decide("rejected")

    def _decide(self, status):
        client_id = self.view.get_selected_request_client_id()
        if client_id is None:
            self.view.show_error("Izaberite zahtev klijenta.")
            return
        try:
            changed = self.fitness_service.decide_client_request(
                self.user.id, client_id, status
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        if not changed:
            self.view.show_error("Zahtev vise nije na cekanju.")
            return
        message = "Zahtev je prihvacen." if status == "accepted" else "Zahtev je odbijen."
        self.view.show_info(message)
        self.refresh()

    def save_exercise(self):
        try:
            self.fitness_service.save_exercise(self.view.get_exercise_data())
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.clear_exercise_form()
        self.view.show_info("Vezba je sacuvana.")
        self.refresh()

    def delete_exercise(self):
        exercise_id = self.view.get_selected_exercise_id()
        if exercise_id is None:
            self.view.show_error("Izaberite vezbu.")
            return
        self.fitness_service.delete_exercise(exercise_id)
        self.view.clear_exercise_form()
        self.refresh()

    def save_equipment(self):
        try:
            self.fitness_service.save_equipment(self.view.get_equipment_data())
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.clear_equipment_form()
        self.view.show_info("Oprema je sacuvana.")
        self.refresh()

    def delete_equipment(self):
        equipment_id = self.view.get_selected_equipment_id()
        if equipment_id is None:
            self.view.show_error("Izaberite opremu.")
            return
        self.fitness_service.delete_equipment(equipment_id)
        self.view.clear_equipment_form()
        self.refresh()

    def create_workout(self):
        client_id = self.view.get_selected_client_id()
        if client_id is None:
            self.view.show_error("Izaberite klijenta.")
            return
        try:
            self.fitness_service.create_workout(
                self.user.id, client_id, self.view.workout_name_var.get().strip(),
                self.view.get_selected_exercise_ids(),
                self.view.scheduled_date_var.get().strip(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Trening je dodeljen klijentu.")
        self.refresh()

    def copy_selected_workout(self):
        workout = self.view.get_selected_trainer_workout()
        client_id = self.view.get_selected_client_id()
        if workout is None or client_id is None:
            self.view.show_error("Izaberite postojeci trening i ciljnog klijenta.")
            return
        try:
            self.fitness_service.copy_workout(self.user.id, workout.id, client_id)
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Trening je kopiran drugom klijentu.")
        self.refresh()

    def mark_workout_missed(self):
        workout_id = self.view.get_selected_trainer_workout_id()
        if workout_id is None:
            self.view.show_error("Izaberite trening.")
            return
        self.fitness_service.mark_workout_missed(self.user.id, workout_id)
        self.view.show_info("Trening je oznacen kao neodradjen.")
        self.refresh()

    def save_client_rating(self):
        client_id = self.view.get_selected_client_id()
        if client_id is None:
            self.view.show_error("Izaberite klijenta.")
            return
        try:
            self.fitness_service.save_client_rating(
                self.user.id, client_id, self.view.client_rating_var.get(),
                self.view.client_rating_comment_var.get(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Interna ocena klijenta je sacuvana i klijent je ne vidi.")
        self.refresh()

    def load_chat(self):
        client_id = self.view.get_selected_client_id()
        rows = [] if client_id is None else self.fitness_service.get_messages(
            self.user.id, client_id
        )
        self.view.show_messages(rows)

    def send_message(self):
        client_id = self.view.get_selected_client_id()
        if client_id is None:
            self.view.show_error("Izaberite klijenta za chat.")
            return
        try:
            self.fitness_service.send_message(
                self.user.id, client_id, self.view.message_var.get()
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.message_var.set("")
        self.load_chat()
