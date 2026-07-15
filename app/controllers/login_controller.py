from app.views.login_view import LoginView


class LoginController:
    def __init__(self, parent, login_service, on_login=None):
        self.login_service = login_service
        self.on_login = on_login
        self.view = LoginView(parent, self)

    def submit(self, username, password):
        try:
            user = self.login_service.login(username, password)
        except ValueError as error:
            self.view.show_error(str(error))
            return

        self.view.close()
        if self.on_login:
            self.on_login(user)
