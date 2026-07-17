from app.controllers.chat_controller import ChatController
from app.views.client_ratings_view import ClientRatingView, ClientRatingsView
from app.views.equipment_management_view import EquipmentManagementView
from app.views.exercise_management_view import ExerciseManagementView
from app.views.trainer_dashboard_view import TrainerDashboardView
from app.views.trainer_profile_view import TrainerProfileView
from app.views.workout_assignment_view import WorkoutAssignmentView


class TrainerDashboardController:
    def __init__(self, parent, user, fitness_service):
        self.user = user
        self.fitness_service = fitness_service
        self.admin_chat_controller = None
        self.client_chat_controller = None
        self.workout_view = None
        self.workout_client = None
        self.exercise_view = None
        self.equipment_view = None
        self.profile_view = None
        self.client_rating_view = None
        self.client_rating_client = None
        self.ratings_view = None
        self.view = TrainerDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        data = self.fitness_service.get_trainer_dashboard_data(self.user.id)
        self.view.show_requests(data["requests"])
        self.view.show_clients(data["clients"])
        self.view.show_center_rent(data["center_rent"])

    def pay_center_rent(self):
        try:
            self.fitness_service.pay_center_rent(self.user.id)
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.refresh()
        self.view.show_info("Mesecni zakup fitnes centra je placen.")

    def accept_selected_request(self):
        self._decide_request("accepted")

    def reject_selected_request(self):
        self._decide_request("rejected")

    def _decide_request(self, status):
        request = self.view.get_selected_request()
        if request is None:
            self.view.show_error("Izaberite zahtev klijenta.")
            return
        try:
            changed = self.fitness_service.decide_client_request(
                self.user.id,
                request.client.id,
                status,
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        if not changed:
            self.view.show_error("Zahtev vise nije na cekanju.")
            return
        if status == "accepted":
            self.view.show_info(
                "Zahtev je prihvacen. Klijent ce se pojaviti desno nakon uplate."
            )
        else:
            self.view.show_info("Zahtev je odbijen.")
        self.refresh()

    def open_request_client_ratings(self):
        request = self.view.get_selected_request()
        if request is None:
            self.view.show_error("Izaberite zahtev klijenta.")
            return
        ratings = self.fitness_service.get_client_ratings(request.client.id)
        self.ratings_view = ClientRatingsView(
            self.view.window,
            request.client.full_name,
            ratings,
        )

    def open_workout_assignment(self):
        client = self.view.get_selected_client()
        if client is None:
            self.view.show_error("Izaberite aktivnog klijenta.")
            return
        if client.missed_count >= 2:
            self.view.show_error(
                "Klijent je u ovoj clanarini propustio dva treninga. "
                "Novi trening moze dobiti tek posle sledece mesecne uplate."
            )
            return
        if self._focus_existing(self.workout_view):
            return
        self.workout_client = client
        self.workout_view = WorkoutAssignmentView(
            self.view.window,
            self,
            client.client.full_name,
        )
        self.workout_view.show_exercises(self.fitness_service.get_exercises())

    def submit_workout(self):
        data = self.workout_view.get_workout_data()
        try:
            self.fitness_service.create_workout(
                self.user.id,
                self.workout_client.client.id,
                data["name"],
                data["exercise_ids"],
                data["deadline"],
            )
        except ValueError as error:
            self.workout_view.show_error(str(error))
            return
        client_name = self.workout_client.client.full_name
        self.close_workout_assignment()
        self.view.show_info(f"Trening je dodeljen klijentu {client_name}.")
        self.refresh()

    def close_workout_assignment(self):
        if self.workout_view:
            self.workout_view.close()
        self.workout_view = None
        self.workout_client = None

    def open_client_chat(self):
        client = self.view.get_selected_client()
        if client is None:
            self.view.show_error("Izaberite aktivnog klijenta.")
            return
        if self.client_chat_controller and self.client_chat_controller.is_open():
            if self.client_chat_controller.other_user_id == client.client.id:
                self.client_chat_controller.focus()
                return
            self.client_chat_controller.close()
        self.client_chat_controller = ChatController(
            self.view.window,
            self.user.id,
            client.client.id,
            client.client.full_name,
            self.fitness_service,
        )

    def open_client_rating(self):
        client = self.view.get_selected_client()
        if client is None:
            self.view.show_error("Izaberite aktivnog klijenta.")
            return
        if self._focus_existing(self.client_rating_view):
            return
        self.client_rating_client = client
        self.client_rating_view = ClientRatingView(
            self.view.window,
            self,
            client.client.full_name,
        )

    def submit_client_rating(self):
        rating, comment = self.client_rating_view.get_rating()
        try:
            self.fitness_service.save_client_rating(
                self.user.id,
                self.client_rating_client.client.id,
                rating,
                comment,
            )
        except ValueError as error:
            self.client_rating_view.show_error(str(error))
            return
        self.close_client_rating()
        self.view.show_info("Ocena klijenta je sacuvana.")

    def close_client_rating(self):
        if self.client_rating_view:
            self.client_rating_view.close()
        self.client_rating_view = None
        self.client_rating_client = None

    def open_exercise_management(self):
        if self._focus_existing(self.exercise_view):
            return
        self.exercise_view = ExerciseManagementView(self.view.window, self)
        self._refresh_exercise_management()

    def _refresh_exercise_management(self):
        self.exercise_view.show_equipment(self.fitness_service.get_equipment())
        self.exercise_view.show_exercises(self.fitness_service.get_exercises())

    def save_exercise(self):
        try:
            self.fitness_service.save_exercise(
                self.exercise_view.get_exercise_data()
            )
        except ValueError as error:
            self.exercise_view.show_error(str(error))
            return
        self.exercise_view.clear_form()
        self._refresh_exercise_management()
        self.exercise_view.show_info("Vezba je sacuvana.")

    def delete_exercise(self):
        exercise_id = self.exercise_view.get_selected_exercise_id()
        if exercise_id is None:
            self.exercise_view.show_error("Izaberite vezbu.")
            return
        self.fitness_service.delete_exercise(exercise_id)
        self.exercise_view.clear_form()
        self._refresh_exercise_management()
        self.exercise_view.show_info("Vezba je obrisana.")

    def close_exercise_management(self):
        if self.exercise_view:
            self.exercise_view.close()
        self.exercise_view = None

    def open_equipment_management(self):
        if self._focus_existing(self.equipment_view):
            return
        self.equipment_view = EquipmentManagementView(self.view.window, self)
        self._refresh_equipment_management()

    def _refresh_equipment_management(self):
        self.equipment_view.show_equipment(self.fitness_service.get_equipment())

    def save_equipment(self):
        try:
            self.fitness_service.save_equipment(
                self.equipment_view.get_equipment_data()
            )
        except ValueError as error:
            self.equipment_view.show_error(str(error))
            return
        self.equipment_view.clear_form()
        self._refresh_equipment_management()
        self.equipment_view.show_info("Sprava je sacuvana.")

    def delete_equipment(self):
        equipment_id = self.equipment_view.get_selected_equipment_id()
        if equipment_id is None:
            self.equipment_view.show_error("Izaberite spravu.")
            return
        self.fitness_service.delete_equipment(equipment_id)
        self.equipment_view.clear_form()
        self._refresh_equipment_management()
        self.equipment_view.show_info("Sprava je obrisana.")

    def close_equipment_management(self):
        if self.equipment_view:
            self.equipment_view.close()
        self.equipment_view = None

    def open_profile(self):
        if self._focus_existing(self.profile_view):
            return
        profile = self.fitness_service.get_trainer_profile(self.user.id)
        self.profile_view = TrainerProfileView(self.view.window, self, profile)

    def save_profile(self):
        try:
            self.fitness_service.save_trainer_profile(
                self.user.id,
                self.profile_view.get_profile_data(),
            )
        except ValueError as error:
            self.profile_view.show_error(str(error))
            return
        self.profile_view.show_info("Profil je sacuvan.")

    def close_profile(self):
        if self.profile_view:
            self.profile_view.close()
        self.profile_view = None

    def open_admin_chat(self):
        try:
            admin_id = self.fitness_service.get_admin_id()
        except ValueError as error:
            self.view.show_error(str(error))
            return
        if self.admin_chat_controller and self.admin_chat_controller.is_open():
            self.admin_chat_controller.focus()
            return
        self.admin_chat_controller = ChatController(
            self.view.window,
            self.user.id,
            admin_id,
            "Administrator",
            self.fitness_service,
        )

    @staticmethod
    def _focus_existing(view):
        if view is None or not view.window.winfo_exists():
            return False
        view.window.lift()
        view.window.focus_force()
        return True
