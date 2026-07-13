from app.controllers.validation import validate_common_registration
from app.models.repositories.user_repository import (
    InitialAdminAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from app.views.registration_views import InitialAdminView


class InitialAdminController:
    """Dozvoljava pravljenje samo prvog administratorskog naloga."""

    def __init__(self, parent, user_repository, on_created=None):
        self.user_repository = user_repository
        self.on_created = on_created
        self.view = InitialAdminView(parent, self)

    def submit(self, data):
        error = validate_common_registration(data)
        if error:
            self.view.show_error(error)
            return

        try:
            self.user_repository.create_initial_admin(
                username=data["username"].strip(),
                password=data["password"],
                first_name=data["first_name"].strip(),
                last_name=data["last_name"].strip(),
                birth_date=data["birth_date"].strip(),
            )
        except (InitialAdminAlreadyExistsError, UsernameAlreadyExistsError) as error:
            self.view.show_error(str(error))
            return

        self.view.show_info("Administrator je napravljen. Sada mozete da se prijavite.")
        if self.on_created:
            self.on_created()
        self.view.close()
