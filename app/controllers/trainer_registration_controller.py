from app.views.registration_views import TrainerRegistrationView


class TrainerRegistrationController:
    def __init__(self, parent, registration_service):
        self.registration_service = registration_service
        self.view = TrainerRegistrationView(parent, self)

    def submit(self, data):
        try:
            self.registration_service.register_trainer(data)
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Zahtev je poslat i ceka odobrenje administratora.")
