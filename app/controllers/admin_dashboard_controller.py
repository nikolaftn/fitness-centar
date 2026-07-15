from app.views.admin_dashboard_view import AdminDashboardView


class AdminDashboardController:
    def __init__(self, parent, user, admin_service):
        self.admin_service = admin_service
        self.view = AdminDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        registrations, trainers = self.admin_service.get_dashboard_data()
        self.view.show_registrations(registrations)
        self.view.show_sorted_trainers(trainers)

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
