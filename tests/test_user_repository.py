import tempfile
import unittest
from pathlib import Path

from app.database import get_connection, initialize_database
from app.models.repositories.trainer_repository import TrainerRepository
from app.models.repositories.user_repository import (
    InitialAdminAlreadyExistsError,
    UserRepository,
    UsernameAlreadyExistsError,
)


class UserRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "fitness-test.db"
        initialize_database(self.database_path)
        self.repository = UserRepository(
            lambda: get_connection(self.database_path)
        )
        self.trainer_repository = TrainerRepository(
            lambda: get_connection(self.database_path)
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_client_is_approved_and_can_authenticate(self):
        created = self.repository.create_client(
            username="marko",
            password="tajna123",
            first_name="Marko",
            last_name="Markovic",
            birth_date="2002-05-20",
        )

        authenticated = self.repository.authenticate("MARKO", "tajna123")

        self.assertEqual("approved", created.registration_status)
        self.assertEqual(created, authenticated)
        self.assertIsNone(self.repository.authenticate("marko", "pogresna"))

        connection = get_connection(self.database_path)
        try:
            stored_password = connection.execute(
                "SELECT password FROM users WHERE username = ?", ("marko",)
            ).fetchone()["password"]
        finally:
            connection.close()
        self.assertEqual("tajna123", stored_password)

    def test_legacy_password_column_is_renamed(self):
        legacy_path = Path(self.temporary_directory.name) / "legacy.db"
        connection = get_connection(legacy_path)
        try:
            connection.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    registration_status TEXT NOT NULL DEFAULT 'approved',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

        initialize_database(legacy_path)

        connection = get_connection(legacy_path)
        try:
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
        finally:
            connection.close()
        self.assertIn("password", columns)
        self.assertNotIn("password_hash", columns)

    def test_trainer_is_pending_and_profile_is_created(self):
        trainer = self.repository.create_trainer(
            username="trener",
            password="trener123",
            first_name="Petar",
            last_name="Petrovic",
            birth_date="1990-03-10",
            education="Fakultet sporta",
            years_of_experience=5,
            price_per_training=1500.0,
        )

        self.assertEqual("trainer", trainer.role)
        self.assertEqual("pending", trainer.registration_status)

        connection = get_connection(self.database_path)
        try:
            profile = connection.execute(
                "SELECT * FROM trainer_profiles WHERE user_id = ?", (trainer.id,)
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual("Fakultet sporta", profile["education"])
        self.assertEqual(5, profile["years_of_experience"])

    def test_duplicate_username_is_rejected_case_insensitively(self):
        self.repository.create_client(
            "korisnik", "lozinka1", "Ime", "Prezime", "2000-01-01"
        )

        with self.assertRaises(UsernameAlreadyExistsError):
            self.repository.create_client(
                "KORISNIK", "lozinka2", "Drugo", "Prezime", "2001-01-01"
            )

    def test_only_one_initial_admin_can_be_created(self):
        admin = self.repository.create_initial_admin(
            "admin", "admin123", "Glavni", "Administrator", "1980-01-01"
        )

        self.assertEqual("admin", admin.role)
        self.assertTrue(self.repository.has_admin())
        self.assertEqual(admin, self.repository.authenticate("admin", "admin123"))
        with self.assertRaises(InitialAdminAlreadyExistsError):
            self.repository.create_initial_admin(
                "drugiadmin", "admin456", "Drugi", "Admin", "1985-01-01"
            )

    def test_pending_trainer_can_be_approved(self):
        trainer = self.repository.create_trainer(
            username="trener2",
            password="trener123",
            first_name="Ana",
            last_name="Anic",
            birth_date="1992-02-02",
            education="Fakultet sporta",
            years_of_experience=4,
            price_per_training=1800.0,
        )

        pending = self.trainer_repository.list_pending_registrations()
        changed = self.trainer_repository.decide_registration(
            trainer.id, "approved"
        )

        self.assertEqual([trainer.id], [item.user_id for item in pending])
        self.assertTrue(changed)
        self.assertEqual(
            "approved",
            self.repository.find_by_username("trener2").registration_status,
        )
        self.assertEqual([], self.trainer_repository.list_pending_registrations())
        self.assertFalse(
            self.trainer_repository.decide_registration(trainer.id, "rejected")
        )


if __name__ == "__main__":
    unittest.main()
