class LoginService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def login(self, username, password):
        username = username.strip()
        if not username or not password:
            raise ValueError("Enter a username and password.")

        user = self.user_repository.authenticate(username, password)
        if user is None:
            raise ValueError("Incorrect username or password.")
        if user.registration_status == "pending":
            raise ValueError("Your registration request is awaiting administrator approval.")
        if user.registration_status == "rejected":
            raise ValueError("Your registration request was rejected, so the account is unavailable.")
        return user
