class LoginService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def login(self, username, password):
        username = username.strip()
        if not username or not password:
            raise ValueError("Unesite korisnicko ime i lozinku.")

        user = self.user_repository.authenticate(username, password)
        if user is None:
            raise ValueError("Pogresno korisnicko ime ili lozinka.")
        if user.registration_status == "pending":
            raise ValueError("Zahtev za registraciju jos ceka odobrenje administratora.")
        if user.registration_status == "rejected":
            raise ValueError("Zahtev za registraciju Vam je odbijen, nalog nije u funkciji.")
        return user
