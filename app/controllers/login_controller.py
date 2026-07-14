from app.views.login_view import LoginView


class LoginController:
    """Obradjuje prijavu iz Login prozora."""

    def __init__(self, parent, user_repository, on_login=None):
        self.user_repository = user_repository
        self.on_login = on_login
        self.view = LoginView(parent, self)

    def submit(self, username, password):
        username = username.strip()
        if not username or not password:
            self.view.show_error("Unesite korisnicko ime i lozinku.")
            return

        user = self.user_repository.authenticate(username, password)
        if user is None:
            self.view.show_error("Pogresno korisnicko ime ili lozinka.")
            return
        if user.registration_status == "pending":
            self.view.show_info("Zahtev za registraciju jos ceka odobrenje administratora.")
            return
        if user.registration_status == "rejected":
            self.view.show_error("Zahtev za registraciju je odbijen.")
            return

        self.view.close()
        if self.on_login:
            self.on_login(user)
