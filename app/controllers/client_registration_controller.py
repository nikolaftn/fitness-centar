from app.controllers.validation import validate_common_registration
from app.models.repositories.user_repository import UsernameAlreadyExistsError
from app.views.registration_views import ClientRegistrationView


class ClientRegistrationController:
    """Registruje klijenta koji odmah dobija odobren nalog."""

    def __init__(self, parent, user_repository, on_registered=None):
        self.user_repository = user_repository
        self.on_registered = on_registered
        self.view = ClientRegistrationView(parent, self)

    def submit(self, data):
        error = validate_common_registration(data)
        if error:
            self.view.show_error(error)
            return

        try:
            self.user_repository.create_client(
                username=data["username"].strip(),
                password=data["password"],
                first_name=data["first_name"].strip(),
                last_name=data["last_name"].strip(),
                birth_date=data["birth_date"].strip(),
            )
        except UsernameAlreadyExistsError as error:
            self.view.show_error(str(error))
            return

        self.view.show_info("Registracija je uspesna. Mozete da se prijavite.")
        if self.on_registered:
            self.on_registered()
        self.view.close()
