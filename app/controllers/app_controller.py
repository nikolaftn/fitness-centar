from app.controllers.admin_dashboard_controller import AdminDashboardController
from app.controllers.client_registration_controller import ClientRegistrationController
from app.controllers.login_controller import LoginController
from app.controllers.role_dashboard_controllers import (
    ClientDashboardController,
    TrainerDashboardController,
)
from app.controllers.trainer_registration_controller import TrainerRegistrationController
from app.models.repositories.fitness_repository import FitnessRepository
from app.models.repositories.trainer_repository import TrainerRepository
from app.models.repositories.user_repository import UserRepository
from app.views.main_view import MainView


class AppController:
    """Povezuje Tkinter prikaz sa Model slojem."""

    def __init__(self):
        self.user_repository = UserRepository()
        self.trainer_repository = TrainerRepository()
        self.fitness_repository = FitnessRepository()
        self.view = MainView(self)

    def run(self):
        self.view.run()

    def open_login(self):
        LoginController(
            self.view.root,
            self.user_repository,
            on_login=self.open_dashboard,
        )

    def open_client_registration(self):
        ClientRegistrationController(
            self.view.root,
            self.user_repository,
        )

    def open_trainer_registration(self):
        TrainerRegistrationController(
            self.view.root,
            self.user_repository,
        )

    def open_dashboard(self, user):
        if user.role == "admin":
            AdminDashboardController(
                self.view.root, user, self.trainer_repository
            )
        elif user.role == "trainer":
            TrainerDashboardController(
                self.view.root,
                user,
                self.fitness_repository,
            )
        elif user.role == "client":
            ClientDashboardController(
                self.view.root,
                user,
                self.fitness_repository,
                self.user_repository,
            )
