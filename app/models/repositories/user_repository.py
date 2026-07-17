import sqlite3
from datetime import datetime

from app.database import get_connection
from app.models.domain.fitness_entities import TrainerProfile, User


class UsernameAlreadyExistsError(ValueError):
    pass


class UserRepository:
    """Radi nad User objektima i cuva njihove izmene u bazi."""

    def __init__(self, application_data, connection_factory=get_connection):
        self.data = application_data
        self.connection_factory = connection_factory

    def find_by_username(self, username):
        wanted_username = username.lower()
        for user in self.data.users.values():
            if user.username.lower() == wanted_username:
                return user
        return None

    def authenticate(self, username, password):
        user = self.find_by_username(username)
        if user is None or user.password != password:
            return None
        return user

    def create_client(self, username, password, first_name, last_name, birth_date):
        return self._create_user(
            username,
            password,
            "client",
            first_name,
            last_name,
            birth_date,
            "approved",
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
        self._check_username(username)
        created_at = self._current_time()
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username, role, first_name, last_name, birth_date,
                    password, registration_status, created_at
                ) VALUES (?, 'trainer', ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    username,
                    first_name,
                    last_name,
                    birth_date,
                    password,
                    created_at,
                ),
            )
            user_id = cursor.lastrowid
            connection.execute(
                """
                INSERT INTO trainer_profiles (
                    user_id, education, years_of_experience, price_per_training
                ) VALUES (?, ?, ?, ?)
                """,
                (user_id, education or None, years_of_experience, price_per_training),
            )
            connection.commit()
        except sqlite3.IntegrityError as error:
            connection.rollback()
            self._raise_readable_integrity_error(error)
            raise
        finally:
            connection.close()

        user = User(
            user_id,
            username,
            "trainer",
            first_name,
            last_name,
            birth_date,
            password,
            "pending",
            created_at,
        )
        profile = TrainerProfile(
            user,
            education or None,
            None,
            None,
            years_of_experience,
            price_per_training,
        )
        self.data.users[user.id] = user
        self.data.trainer_profiles[user.id] = profile
        return user

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
        self._check_username(username)
        created_at = self._current_time()
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username, role, first_name, last_name, birth_date,
                    password, registration_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    role,
                    first_name,
                    last_name,
                    birth_date,
                    password,
                    registration_status,
                    created_at,
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError as error:
            connection.rollback()
            self._raise_readable_integrity_error(error)
            raise
        finally:
            connection.close()

        user = User(
            cursor.lastrowid,
            username,
            role,
            first_name,
            last_name,
            birth_date,
            password,
            registration_status,
            created_at,
        )
        self.data.users[user.id] = user
        return user

    def update_profile(self, user_id, first_name, last_name, birth_date):
        user = self.data.users.get(user_id)
        if user is None:
            raise ValueError("Korisnik nije pronadjen.")

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?, birth_date = ?
                WHERE id = ?
                """,
                (first_name, last_name, birth_date, user.id),
            )
            connection.commit()
        finally:
            connection.close()

        user.first_name = first_name
        user.last_name = last_name
        user.birth_date = birth_date
        return user

    def _check_username(self, username):
        if self.find_by_username(username) is not None:
            raise UsernameAlreadyExistsError("Korisnicko ime je vec zauzeto.")

    @staticmethod
    def _current_time():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _raise_readable_integrity_error(error):
        if "users.username" in str(error):
            raise UsernameAlreadyExistsError(
                "Korisnicko ime je vec zauzeto."
            ) from error
