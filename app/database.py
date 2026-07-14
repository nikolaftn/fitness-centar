import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIRECTORY = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIRECTORY / "fitness.db"


def get_connection(database_path=DATABASE_PATH):
    """Otvara konekciju sa lokalnom SQLite bazom."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def add_test_data(database_path=DATABASE_PATH):
    """Dodaje osnovne test naloge ako vec ne postoje."""
    connection = get_connection(database_path)

    try:
        connection.execute(
            """
            INSERT INTO users (
                username, role, first_name, last_name, birth_date,
                password, registration_status
            )
            SELECT 'admin', 'admin', 'Glavni', 'Administrator', '1980-01-01',
                   'admin123', 'approved'
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin')
            """
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO users (
                username, role, first_name, last_name, birth_date,
                password, registration_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "trener1",
                    "trainer",
                    "Marko",
                    "Markovic",
                    "1988-05-14",
                    "trener123",
                    "approved",
                ),
                (
                    "trener2",
                    "trainer",
                    "Ana",
                    "Anic",
                    "1992-09-22",
                    "trener123",
                    "pending",
                ),
                (
                    "klijent1",
                    "client",
                    "Petar",
                    "Petrovic",
                    "2001-03-10",
                    "klijent123",
                    "approved",
                ),
                (
                    "klijent2",
                    "client",
                    "Jelena",
                    "Jovanovic",
                    "1999-11-08",
                    "klijent123",
                    "approved",
                ),
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO trainer_profiles (
                user_id, education, years_of_experience, price_per_training
            )
            SELECT id, ?, ?, ? FROM users WHERE username = ?
            """,
            [
                ("Fakultet sporta", 8, 2000.0, "trener1"),
                ("Visoka sportska skola", 4, 1500.0, "trener2"),
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO exercises (name, description)
            VALUES (?, ?)
            """,
            [
                ("Cucanj", "Osnovna vezba za noge i gluteus."),
                ("Sklek", "Vezba za grudi, ramena i triceps."),
                ("Plank", "Staticka vezba za stabilizaciju trupa."),
            ],
        )
        connection.commit()
    finally:
        connection.close()


def initialize_database(database_path=DATABASE_PATH):
    """Pravi data folder i osnovne tabele za korisnike ako ne postoje."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection(database_path)

    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('admin', 'trainer', 'client')),
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                password TEXT NOT NULL,
                registration_status TEXT NOT NULL DEFAULT 'approved'
                    CHECK (registration_status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS trainer_profiles (
                user_id INTEGER PRIMARY KEY,
                education TEXT,
                years_of_experience INTEGER NOT NULL DEFAULT 0
                    CHECK (years_of_experience >= 0),
                price_per_training REAL NOT NULL
                    CHECK (price_per_training >= 0),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS trainer_client_relations (
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                monthly_price REAL CHECK (monthly_price >= 0),
                expiration_date TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
                workouts_per_week INTEGER NOT NULL
                    CHECK (workouts_per_week BETWEEN 1 AND 7),
                goals TEXT,
                height_cm REAL,
                weight_kg REAL,
                training_location TEXT CHECK (
                    training_location IN ('gym', 'home', 'both')
                ),
                health_conditions TEXT,
                PRIMARY KEY (trainer_id, client_id),
                FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS client_ratings (
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (trainer_id, client_id),
                FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS trainer_ratings (
                client_id INTEGER NOT NULL,
                trainer_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (client_id, trainer_id),
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL CHECK (category IN ('machine', 'prop')),
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                video_url TEXT
            );

            CREATE TABLE IF NOT EXISTS exercise_equipment (
                exercise_id INTEGER NOT NULL,
                equipment_id INTEGER NOT NULL,
                PRIMARY KEY (exercise_id, equipment_id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trainer_id, client_id)
                    REFERENCES trainer_client_relations(trainer_id, client_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                scheduled_date TEXT,
                status TEXT NOT NULL DEFAULT 'assigned'
                    CHECK (status IN ('assigned', 'completed', 'missed')),
                FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS workout_exercises (
                workout_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                exercise_order INTEGER NOT NULL CHECK (exercise_order >= 1),
                sets INTEGER CHECK (sets > 0),
                repetitions INTEGER CHECK (repetitions > 0),
                duration_minutes INTEGER CHECK (duration_minutes > 0),
                PRIMARY KEY (workout_id, exercise_id),
                UNIQUE (workout_id, exercise_order),
                FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS workout_ratings (
                workout_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (workout_id, client_id),
                FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exercise_ratings (
                workout_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (workout_id, exercise_id, client_id),
                FOREIGN KEY (workout_id, exercise_id)
                    REFERENCES workout_exercises(workout_id, exercise_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exercise_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                video_url TEXT NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workout_id, exercise_id)
                    REFERENCES workout_exercises(workout_id, exercise_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                period TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'paid'
                    CHECK (status IN ('paid', 'pending', 'failed')),
                paid_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (trainer_id, client_id, period),
                FOREIGN KEY (trainer_id, client_id)
                    REFERENCES trainer_client_relations(trainer_id, client_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        user_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "password_hash" in user_columns and "password" not in user_columns:
            connection.execute(
                "ALTER TABLE users RENAME COLUMN password_hash TO password"
            )

        exercise_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(exercises)").fetchall()
        }
        if "video_url" not in exercise_columns:
            connection.execute("ALTER TABLE exercises ADD COLUMN video_url TEXT")
        connection.commit()
    finally:
        connection.close()



# Remove-Item .\data\fitness.db - ovo je za brisanje baze u shellu se kuca
