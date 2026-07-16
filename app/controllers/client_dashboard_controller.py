from app.controllers.chat_controller import ChatController
from app.views.client_dashboard_view import ClientDashboardView
from app.views.client_profile_view import ClientProfileView
from app.views.client_workouts_view import ClientWorkoutsView
from app.views.notification_view import NotificationView
from app.views.rating_view import RatingView


class ClientDashboardController:
    def __init__(self, parent, user, fitness_service):
        self.user = user
        self.fitness_service = fitness_service
        self.chat_controller = None
        self.workouts_view = None
        self.workouts_relation = None
        self.rating_view = None
        self.rating_type = None
        self.rating_target = None
        self.profile_view = None
        self.notification_view = None
        self.notifications = []
        self.current_notification = None

        self.view = ClientDashboardView(parent, self, user)
        self.refresh()
        self.open_unread_notifications()

    def refresh(self):
        data = self.fitness_service.get_client_dashboard_data(self.user.id)
        self.view.show_trainers(data["trainers"])
        self.view.show_relations(data["relations"])

    def send_request(self):
        trainer = self.view.get_selected_trainer()
        if trainer is None:
            self.view.show_error("Prvo izaberite trenera.")
            return
        try:
            self.fitness_service.send_client_request(
                trainer["id"],
                self.user.id,
                self.view.get_request_data(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Zahtev je poslat treneru.")
        self.refresh()

    def open_workouts(self):
        relation = self._get_active_relation()
        if relation is None:
            return
        try:
            workouts = self.fitness_service.get_client_workouts(
                self.user.id,
                relation.trainer_id,
            )
        except ValueError as error:
            self.view.show_error(str(error))
            self.refresh()
            return
        self.workouts_relation = relation
        self.workouts_view = ClientWorkoutsView(
            self.view.window,
            self,
            relation.trainer_name,
        )
        self.workouts_view.show_workouts(workouts)

    def load_workout_exercises(self, workout):
        exercises = self.fitness_service.get_workout_exercises(
            workout.id,
            self.user.id,
        )
        self.workouts_view.show_exercises(exercises)

    def toggle_exercise(self, exercise_id, completed):
        workout = self.workouts_view.get_selected_workout()
        try:
            self.fitness_service.set_exercise_completed(
                workout.id,
                exercise_id,
                self.user.id,
                completed,
            )
        except ValueError as error:
            self.workouts_view.show_error(str(error))
            self.load_workout_exercises(workout)
            return
        self.workouts_view.show_info("Status vezbe je sacuvan.")
        self.load_workout_exercises(workout)

    def open_workout_rating(self):
        workout = self.workouts_view.get_selected_workout()
        if workout is None:
            self.workouts_view.show_error("Izaberite trening.")
            return
        self._open_rating("workout", workout, f"Oceni trening: {workout.name}")

    def open_exercise_rating(self, exercise):
        self._open_rating("exercise", exercise, f"Oceni vezbu: {exercise.name}")

    def open_trainer_rating(self):
        relation = self._get_active_relation()
        if relation is None:
            return
        self._open_rating(
            "trainer",
            relation,
            f"Oceni trenera: {relation.trainer_name}",
        )

    def _open_rating(self, rating_type, target, title):
        if self.rating_view and self.rating_view.window.winfo_exists():
            self.rating_view.window.lift()
            return
        self.rating_type = rating_type
        self.rating_target = target
        parent = self.workouts_view.window if rating_type != "trainer" else self.view.window
        self.rating_view = RatingView(
            parent,
            title,
            self.submit_rating,
            self.close_rating,
        )

    def submit_rating(self):
        rating, comment = self.rating_view.get_data()
        try:
            if self.rating_type == "trainer":
                self.fitness_service.rate_trainer(
                    self.rating_target.trainer_id,
                    self.user.id,
                    rating,
                    comment,
                )
            elif self.rating_type == "workout":
                self.fitness_service.rate_workout(
                    self.rating_target.id,
                    self.user.id,
                    rating,
                    comment,
                )
            else:
                workout = self.workouts_view.get_selected_workout()
                self.fitness_service.rate_exercise(
                    workout.id,
                    self.rating_target.id,
                    self.user.id,
                    rating,
                    comment,
                )
        except ValueError as error:
            self.rating_view.show_error(str(error))
            return

        rating_type = self.rating_type
        self.close_rating()
        if rating_type == "trainer":
            self.view.show_info("Ocena trenera je sacuvana ili azurirana.")
            self.refresh()
        else:
            self._refresh_workouts()
            self.workouts_view.show_info("Ocena je sacuvana ili azurirana.")

    def close_rating(self):
        if self.rating_view:
            self.rating_view.close()
        self.rating_view = None
        self.rating_type = None
        self.rating_target = None

    def _refresh_workouts(self):
        workouts = self.fitness_service.get_client_workouts(
            self.user.id,
            self.workouts_relation.trainer_id,
        )
        self.workouts_view.selected_workout = None
        self.workouts_view.workout_title.configure(text="Izaberite trening.")
        self.workouts_view.show_workouts(workouts)
        self.workouts_view.show_exercises([])

    def close_workouts(self):
        if self.rating_view:
            self.close_rating()
        if self.workouts_view:
            self.workouts_view.close()
        self.workouts_view = None
        self.workouts_relation = None

    def pay_membership(self):
        relation = self.view.get_selected_relation()
        if relation is None or relation.status != "accepted":
            self.view.show_error("Trener prvo mora da prihvati zahtev.")
            return
        if relation.is_paid:
            self.view.show_error("Clanarina je vec placena.")
            return
        try:
            self.fitness_service.pay_membership(
                relation.trainer_id,
                self.user.id,
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Clanarina je placena i vazi narednih mesec dana.")
        self.refresh()

    def open_chat(self):
        relation = self._get_active_relation()
        if relation is None:
            return
        if self.chat_controller and self.chat_controller.is_open():
            if self.chat_controller.other_user_id == relation.trainer_id:
                self.chat_controller.focus()
                return
            self.chat_controller.close()
        self.chat_controller = ChatController(
            self.view.window,
            self.user.id,
            relation.trainer_id,
            relation.trainer_name,
            self.fitness_service,
        )

    def _get_active_relation(self):
        relation = self.view.get_selected_relation()
        if relation is None:
            self.view.show_error("Izaberite trenera iz svojih odnosa.")
            return None
        if relation.status != "accepted" or not relation.is_paid:
            self.view.show_error("Ova clanarina nije aktivna.")
            return None
        return relation

    def open_profile(self):
        if self.profile_view and self.profile_view.window.winfo_exists():
            self.profile_view.window.lift()
            return
        self.profile_view = ClientProfileView(self.view.window, self, self.user)

    def save_profile(self):
        try:
            self.user = self.fitness_service.update_client_profile(
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

    def open_unread_notifications(self):
        self.notifications = list(
            self.fitness_service.get_unread_notifications(self.user.id)
        )
        if not self.notifications:
            return
        self.notification_view = NotificationView(self.view.window, self)
        self._show_next_notification()

    def _show_next_notification(self):
        if not self.notifications:
            self.close_notifications()
            self.refresh()
            return
        self.current_notification = self.notifications.pop(0)
        self.notification_view.show_notification(self.current_notification)

    def mark_current_notification_read(self):
        self.fitness_service.mark_notification_read(
            self.current_notification.id,
            self.user.id,
        )
        self._show_next_notification()

    def close_notifications(self):
        if self.notification_view:
            self.notification_view.close()
        self.notification_view = None
        self.current_notification = None
        self.notifications = []
