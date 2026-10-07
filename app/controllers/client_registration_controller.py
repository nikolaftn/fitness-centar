from app.views.registration_views import ClientRegistrationView


class ClientRegistrationController:
    def __init__(self, parent, registration_service):
        self.registration_service = registration_service
        self.view = ClientRegistrationView(parent, self)

    def submit(self, data):
        try:
            self.registration_service.register_client(data)
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.show_info("Registration successful. You can now log in.")
