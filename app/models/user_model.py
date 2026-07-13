from app.models.repositories.user_repository import UserRepository


class UserModel:
    """Kompatibilni ulaz u korisnicki Model sloj."""

    @staticmethod
    def count_users():
        return UserRepository().count_users()
