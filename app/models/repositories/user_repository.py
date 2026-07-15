import sqlite3

from app.database import get_connection
from app.models.domain.user import User


class UsernameAlreadyExistsError(ValueError):
    """Korisnicko ime vec postoji u bazi."""


class UserRepository:
    """Svi SQL upiti vezani za korisnike i njihove profile."""

    def __init__(self, connection_factory=get_connection):
        self.connection_factory = connection_factory

    @staticmethod
    def _to_user(row):
        if row is None:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            role=row["role"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            birth_date=row["birth_date"],
            registration_status=row["registration_status"],
        )

    def find_by_username(self, username):
        connection = self.connection_factory()
        try:
            row = connection.execute(
                """
                SELECT id, username, role, first_name, last_name, birth_date,
                       registration_status
                FROM users
                WHERE username = ? COLLATE NOCASE
                """,
                (username,),
            ).fetchone()
            return self._to_user(row)
        finally:
            connection.close()

    def create_client(self, username, password, first_name, last_name, birth_date):
        return self._create_user(
            username=username,
            password=password,
            role="client",
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            registration_status="approved",
        )

    def create_trainer(
        self,
        username,
        password,
        first_name,
        last_name,
        birth_date,
        education,
        years_of_experience,
        price_per_training,
    ):
        connection = self.connection_factory()
        try:
            user_id = self._insert_user(
                connection=connection,
                username=username,
                password=password,
                role="trainer",
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                registration_status="pending",
            )
            connection.execute(
                """
                INSERT INTO trainer_profiles (
                    user_id, education, years_of_experience, price_per_training
                ) VALUES (?, ?, ?, ?)
                """,
                (user_id, education or None, years_of_experience, price_per_training),
            )
            connection.commit()
            return self._find_by_id(connection, user_id)
        except sqlite3.IntegrityError as error:
            connection.rollback()
            self._raise_readable_integrity_error(error)
            raise
        finally:
            connection.close()

    def _create_user(
        self,
        username,
        password,
        role,
        first_name,
        last_name,
        birth_date,
        registration_status,
    ):
        connection = self.connection_factory()
        try:
            user_id = self._insert_user(
                connection=connection,
                username=username,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                registration_status=registration_status,
            )
            connection.commit()
            return self._find_by_id(connection, user_id)
        except sqlite3.IntegrityError as error:
            connection.rollback()
            self._raise_readable_integrity_error(error)
            raise
        finally:
            connection.close()

    def _insert_user(
        self,
        connection,
        username,
        password,
        role,
        first_name,
        last_name,
        birth_date,
        registration_status,
    ):
        username_exists = connection.execute(
            "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
        if username_exists:
            raise UsernameAlreadyExistsError("Korisnicko ime je vec zauzeto.")

        cursor = connection.execute(
            """
            INSERT INTO users (
                username, role, first_name, last_name, birth_date,
                password, registration_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                role,
                first_name,
                last_name,
                birth_date,
                password,
                registration_status,
            ),
        )
        return cursor.lastrowid

    @staticmethod
    def _raise_readable_integrity_error(error):
        if "users.username" in str(error):
            raise UsernameAlreadyExistsError(
                "Korisnicko ime je vec zauzeto."
            ) from error

    def _find_by_id(self, connection, user_id):
        row = connection.execute(
            """
            SELECT id, username, role, first_name, last_name, birth_date,
                   registration_status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        return self._to_user(row)

    def authenticate(self, username, password):
        connection = self.connection_factory()
        try:
            row = connection.execute(
                """
                SELECT id, username, role, first_name, last_name, birth_date,
                       registration_status, password
                FROM users
                WHERE username = ? COLLATE NOCASE
                """,
                (username,),
            ).fetchone()
            if row is None or row["password"] != password:
                return None
            return self._to_user(row)
        finally:
            connection.close()

    def update_profile(self, user_id, first_name, last_name, birth_date):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?, birth_date = ?
                WHERE id = ?
                """,
                (first_name, last_name, birth_date, user_id),
            )
            connection.commit()
            return self._find_by_id(connection, user_id)
        finally:
            connection.close()
