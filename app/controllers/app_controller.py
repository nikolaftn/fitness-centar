from app.controllers.admin_dashboard_controller import AdminDashboardController
from app.controllers.client_registration_controller import ClientRegistrationController
from app.controllers.login_controller import LoginController
from app.controllers.client_dashboard_controller import ClientDashboardController
from app.controllers.trainer_dashboard_controller import TrainerDashboardController
from app.controllers.trainer_registration_controller import TrainerRegistrationController
from app.models.repositories.fitness_repository import FitnessRepository
from app.models.repositories.trainer_repository import TrainerRepository
from app.models.repositories.user_repository import UserRepository
from app.models.services.admin_service import AdminService
from app.models.services.login_service import LoginService
from app.models.services.fitness_service import FitnessService
from app.models.services.registration_service import RegistrationService
from app.views.main_view import MainView


class AppController:
    """Povezuje Tkinter prikaz sa Model slojem."""

    def __init__(self, application_data):
        self.application_data = application_data
        self.user_repository = UserRepository(application_data)
        self.trainer_repository = TrainerRepository(application_data)
        self.fitness_repository = FitnessRepository(application_data)
        self.login_service = LoginService(self.user_repository)
        self.registration_service = RegistrationService(self.user_repository)
        self.admin_service = AdminService(
            self.trainer_repository, self.fitness_repository
        )
        self.fitness_service = FitnessService(
            self.fitness_repository, self.user_repository
        )
        self.view = MainView(self)

    def run(self):
        self.view.run()

    def open_login(self):
        LoginController(
            self.view.root,
            self.login_service,
            on_login=self.open_dashboard,
        )

    def open_client_registration(self):
        ClientRegistrationController(
            self.view.root,
            self.registration_service,
        )

    def open_trainer_registration(self):
        TrainerRegistrationController(
            self.view.root,
            self.registration_service,
        )

    def open_dashboard(self, user):
        if user.role == "admin":
            AdminDashboardController(
                self.view.root, user, self.admin_service
            )
        elif user.role == "trainer":
            TrainerDashboardController(
                self.view.root,
                user,
                self.fitness_service,
            )
        elif user.role == "client":
            ClientDashboardController(
                self.view.root,
                user,
                self.fitness_service,
            )
