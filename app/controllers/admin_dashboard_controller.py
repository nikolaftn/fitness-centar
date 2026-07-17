from app.controllers.chat_controller import ChatController
from app.views.admin_dashboard_view import AdminDashboardView


class AdminDashboardController:
    def __init__(self, parent, user, admin_service):
        self.user = user
        self.admin_service = admin_service
        self.chat_controller = None
        self.view = AdminDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        registrations, trainers, center_rents = (
            self.admin_service.get_dashboard_data()
        )
        self.view.show_registrations(registrations)
        self.view.show_sorted_trainers(trainers)
        self.view.show_center_rents(center_rents)

    def delete_selected_trainer(self):
        trainer_id = self.view.get_selected_existing_trainer_id()
        if trainer_id is None:
            self.view.show_error(
                "Prvo izaberite odobrenog trenera iz tabele sa ocenama."
            )
            return
        try:
            self.admin_service.delete_trainer(trainer_id)
        except ValueError as error:
            self.view.show_error(str(error))
            return
        if (
            self.chat_controller
            and self.chat_controller.other_user_id == trainer_id
            and self.chat_controller.is_open()
        ):
            self.chat_controller.close()
        self.refresh()
        self.view.show_info("Trener je uklonjen.")

    def open_trainer_chat(self):
        trainer_id = self.view.get_selected_existing_trainer_id()
        trainer_name = self.view.get_selected_existing_trainer_name()
        if trainer_id is None:
            self.view.show_error(
                "Prvo izaberite odobrenog trenera iz tabele sa ocenama."
            )
            return

        if self.chat_controller and self.chat_controller.is_open():
            if self.chat_controller.other_user_id == trainer_id:
                self.chat_controller.focus()
                return
            self.chat_controller.close()

        self.chat_controller = ChatController(
            self.view.window,
            self.user.id,
            trainer_id,
            trainer_name,
            self.admin_service,
        )

    def approve_selected(self):
        self._decide_selected("approved")

    def reject_selected(self):
        self._decide_selected("rejected")

    def _decide_selected(self, decision):
        trainer_id = self.view.get_selected_trainer_id()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite zahtev trenera iz tabele.")
            return
        try:
            changed = self.admin_service.decide_trainer_registration(
                trainer_id, decision
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        if not changed:
            self.view.show_error("Zahtev vise nije na cekanju. Osvezite tabelu.")
            return
        result = "odobren" if decision == "approved" else "odbijen"
        self.view.show_info(f"Zahtev trenera je {result}.")
        self.refresh()
