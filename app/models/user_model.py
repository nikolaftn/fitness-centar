from app.database import get_connection


class UserModel:
    """Rad sa tabelom users i pravilima vezanim za korisnike."""

    @staticmethod
    def count_users():
        connection = get_connection()

        try:
            row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
            return row["total"]
        finally:
            connection.close()
