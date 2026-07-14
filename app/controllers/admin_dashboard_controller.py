from app.views.admin_dashboard_view import AdminDashboardView


class AdminDashboardController:
    """Povezuje administratorski prozor sa Trainer Repository slojem."""

    def __init__(self, parent, user, trainer_repository):
        self.trainer_repository = trainer_repository
        self.view = AdminDashboardView(parent, self, user)
        self.refresh()

    def refresh(self):
        registrations = self.trainer_repository.list_pending_registrations()
        self.view.show_registrations(registrations)

    def approve_selected(self):
        self._decide_selected("approved")

    def reject_selected(self):
        self._decide_selected("rejected")

    def _decide_selected(self, decision):
        trainer_id = self.view.get_selected_trainer_id()
        if trainer_id is None:
            self.view.show_error("Prvo izaberite zahtev trenera iz tabele.")
            return
        changed = self.trainer_repository.decide_registration(trainer_id, decision)
        if not changed:
            self.view.show_error("Zahtev vise nije na cekanju. Osvezite tabelu.")
            return

        result = "odobren" if decision == "approved" else "odbijen"
        self.view.show_info(f"Zahtev trenera je {result}.")
        self.refresh()
