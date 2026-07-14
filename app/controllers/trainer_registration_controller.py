from app.controllers.validation import validate_common_registration
from app.models.repositories.user_repository import UsernameAlreadyExistsError
from app.views.registration_views import TrainerRegistrationView


class TrainerRegistrationController:
    """Kreira zahtev trenera koji administrator naknadno odobrava."""

    def __init__(self, parent, user_repository, on_registered=None):
        self.user_repository = user_repository
        self.on_registered = on_registered
        self.view = TrainerRegistrationView(parent, self)

    def submit(self, data):
        error = validate_common_registration(data)
        if error:
            self.view.show_error(error)
            return

        try:
            years_of_experience = int(data["years_of_experience"].strip())
            price_per_training = float(
                data["price_per_training"].strip().replace(",", ".")
            )
        except ValueError:
            self.view.show_error("Godine iskustva i cena moraju biti brojevi.")
            return
        if years_of_experience < 0 or price_per_training < 0:
            self.view.show_error("Godine iskustva i cena ne mogu biti negativni.")
            return

        try:
            self.user_repository.create_trainer(
                username=data["username"].strip(),
                password=data["password"],
                first_name=data["first_name"].strip(),
                last_name=data["last_name"].strip(),
                birth_date=data["birth_date"].strip(),
                education=data["education"].strip(),
                years_of_experience=years_of_experience,
                price_per_training=price_per_training,
            )
        except UsernameAlreadyExistsError as error:
            self.view.show_error(str(error))
            return

        self.view.show_info("Zahtev je poslat i ceka odobrenje administratora.")
        if self.on_registered:
            self.on_registered()
