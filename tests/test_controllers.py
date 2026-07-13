import unittest
from types import SimpleNamespace

from app.controllers.client_registration_controller import (
    ClientRegistrationController,
)
from app.controllers.login_controller import LoginController
from app.controllers.trainer_registration_controller import (
    TrainerRegistrationController,
)


class FakeView:
    def __init__(self):
        self.errors = []
        self.infos = []
        self.closed = False

    def show_error(self, message):
        self.errors.append(message)

    def show_info(self, message):
        self.infos.append(message)

    def close(self):
        self.closed = True


class FakeRepository:
    def __init__(self, authenticated_user=None):
        self.authenticated_user = authenticated_user
        self.created_clients = []
        self.created_trainers = []

    def authenticate(self, _username, _password):
        return self.authenticated_user

    def create_client(self, **data):
        self.created_clients.append(data)

    def create_trainer(self, **data):
        self.created_trainers.append(data)


def make_controller(controller_class, repository):
    controller = object.__new__(controller_class)
    controller.user_repository = repository
    controller.on_registered = None
    controller.on_created = None
    controller.on_login = None
    controller.view = FakeView()
    return controller


class ControllerTest(unittest.TestCase):
    def test_client_registration_rejects_invalid_date(self):
        repository = FakeRepository()
        controller = make_controller(ClientRegistrationController, repository)

        controller.submit(
            {
                "username": "marko",
                "password": "tajna123",
                "password_confirmation": "tajna123",
                "first_name": "Marko",
                "last_name": "Markovic",
                "birth_date": "20.05.2002",
            }
        )

        self.assertEqual([], repository.created_clients)
        self.assertIn("GGGG-MM-DD", controller.view.errors[0])

    def test_trainer_registration_creates_pending_request_data(self):
        repository = FakeRepository()
        controller = make_controller(TrainerRegistrationController, repository)

        controller.submit(
            {
                "username": "trener",
                "password": "tajna123",
                "password_confirmation": "tajna123",
                "first_name": "Petar",
                "last_name": "Petrovic",
                "birth_date": "1990-03-10",
                "education": "Fakultet sporta",
                "years_of_experience": "5",
                "price_per_training": "1500,50",
            }
        )

        self.assertEqual(1, len(repository.created_trainers))
        self.assertEqual(
            1500.5, repository.created_trainers[0]["price_per_training"]
        )
        self.assertTrue(controller.view.closed)

    def test_pending_trainer_cannot_finish_login(self):
        user = SimpleNamespace(
            registration_status="pending",
            full_name="Petar Petrovic",
            role="trainer",
        )
        controller = make_controller(LoginController, FakeRepository(user))

        controller.submit("trener", "tajna123")

        self.assertFalse(controller.view.closed)
        self.assertIn("ceka odobrenje", controller.view.infos[0])

    def test_approved_user_is_forwarded_after_login(self):
        user = SimpleNamespace(
            registration_status="approved",
            full_name="Marko Markovic",
            role="client",
        )
        controller = make_controller(LoginController, FakeRepository(user))
        forwarded_users = []
        controller.on_login = forwarded_users.append

        controller.submit("marko", "tajna123")

        self.assertTrue(controller.view.closed)
        self.assertEqual([user], forwarded_users)


if __name__ == "__main__":
    unittest.main()
