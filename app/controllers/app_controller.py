from app.models.user_model import UserModel
from app.views.main_view import MainView


class AppController:
    """Povezuje Tkinter prikaz sa Model slojem."""

    def __init__(self):
        self.view = MainView(self)

    def run(self):
        self.view.run()

    def get_user_count(self):
        return UserModel.count_users()

    def show_not_implemented_message(self, feature_name):
        self.view.show_info(
            "Nedostupna funkcionalnost",
            f"Funkcionalnost '{feature_name}' jos nije napravljena.",
        )
