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
    """Dodaje kompletne test podatke za proveru klijentskih i trenerskih funkcija."""
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
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
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
                ("trener1", "trainer", "Marko", "Markovic", "1988-05-14", "trener123", "approved"),
                ("trener2", "trainer", "Ana", "Anic", "1992-09-22", "trener123", "approved"),
                ("trener_pending", "trainer", "Nikola", "Nikolic", "1995-02-18", "trener123", "pending"),
                ("trener_rejected", "trainer", "Milan", "Milic", "1990-07-11", "trener123", "rejected"),
                ("klijent1", "client", "Petar", "Petrovic", "2001-03-10", "klijent123", "approved"),
                ("klijent2", "client", "Jelena", "Jovanovic", "1999-11-08", "klijent123", "approved"),
                ("klijent3", "client", "Luka", "Lukic", "2002-06-15", "klijent123", "approved"),
                ("klijent4", "client", "Sara", "Saric", "2000-12-03", "klijent123", "approved"),
            ],
        )

        connection.executemany(
            """
            INSERT INTO trainer_profiles (
                user_id, education, diploma_license, biography,
                years_of_experience, price_per_training
            )
            SELECT id, ?, ?, ?, ?, ? FROM users WHERE username = ?
            ON CONFLICT(user_id) DO UPDATE SET
                education=excluded.education,
                diploma_license=excluded.diploma_license,
                biography=excluded.biography,
                years_of_experience=excluded.years_of_experience,
                price_per_training=excluded.price_per_training
            """,
            [
                ("Fakultet sporta i fizickog vaspitanja", "FIT-2020-001", "Trener snage i kondicije.", 8, 2000.0, "trener1"),
                ("Visoka sportska skola", "LIC-2022-114", "Pilates, mobilnost i funkcionalni trening.", 4, 1500.0, "trener2"),
                ("Fakultet sporta", "CEKA-PROVERU", "Zahtev ceka odobrenje administratora.", 2, 1200.0, "trener_pending"),
                ("Kurs fitnes instruktora", "ODBIJENA-LICENCA", "Primer odbijenog zahteva.", 1, 1000.0, "trener_rejected"),
            ],
        )

        connection.executemany(
            """INSERT OR IGNORE INTO equipment(name, category, description)
               VALUES (?, ?, ?)""",
            [
                ("Traka za trcanje", "machine", "Kardio sprava sa podesavanjem brzine."),
                ("Leg press", "machine", "Sprava za trening nogu."),
                ("Lat masina", "machine", "Sprava za ledja."),
                ("Bucice", "prop", "Par bucica razlicitih tezina."),
                ("Prostirka", "prop", "Prostirka za vezbe na podu."),
                ("Elasticna traka", "prop", "Rekvizit za aktivaciju i mobilnost."),
            ],
        )

        connection.executemany(
            """
            INSERT INTO exercises(
                name, description, video_url, duration_minutes, equipment_id
            )
            VALUES (?, ?, ?, ?, (SELECT id FROM equipment WHERE name=?))
            ON CONFLICT(name) DO UPDATE SET
                description=excluded.description,
                video_url=excluded.video_url,
                duration_minutes=excluded.duration_minutes,
                equipment_id=excluded.equipment_id
            """,
            [
                ("Cucanj", "Osnovna vezba za noge i gluteus.", "https://example.com/video/cucanj", 10, "Elasticna traka"),
                ("Sklek", "Vezba za grudi, ramena i triceps.", "https://example.com/video/sklek", 8, "Prostirka"),
                ("Plank", "Staticka vezba za stabilizaciju trupa.", "https://example.com/video/plank", 5, "Prostirka"),
                ("Iskorak", "Jednonozna vezba za noge i ravnotezu.", "https://example.com/video/iskorak", 10, "Bucice"),
                ("Veslanje bucicama", "Vezba za ledja uz bucice.", "https://example.com/video/veslanje", 12, "Bucice"),
            ],
        )

        # Odnosi: prihvacen, na cekanju, odbijen i klijent sa dva propustena treninga.
        connection.executemany(
            """
            INSERT INTO trainer_client_relations(
                trainer_id, client_id, monthly_price, expiration_date, status,
                workouts_per_week, goals, height_cm, weight_kg,
                training_location, health_conditions
            )
            SELECT t.id, c.id, ?, ?, ?, ?, ?, ?, ?, ?, ?
            FROM users t, users c WHERE t.username=? AND c.username=?
            ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                monthly_price=excluded.monthly_price,
                expiration_date=excluded.expiration_date,
                status=excluded.status,
                workouts_per_week=excluded.workouts_per_week,
                goals=excluded.goals,
                height_cm=excluded.height_cm,
                weight_kg=excluded.weight_kg,
                training_location=excluded.training_location,
                health_conditions=excluded.health_conditions
            """,
            [
                (24000.0, "2026-08-31", "accepted", 3, "Povecanje snage i misicne mase", 182, 82, "gym", "Nema", "trener1", "klijent1"),
                (16000.0, None, "pending", 2, "Mrsavljenje 6 kg", 168, 73, "both", "Povremeni bol u kolenu", "trener1", "klijent2"),
                (16000.0, "2026-08-31", "accepted", 2, "Bolja kondicija", 178, 91, "gym", "Nema", "trener1", "klijent3"),
                (12000.0, "2026-08-31", "accepted", 2, "Mobilnost i drzanje", 165, 58, "home", "Blaga skolioza", "trener2", "klijent4"),
                (6000.0, None, "rejected", 1, "Pocetnicki program", 170, 65, "home", "Nema", "trener2", "klijent2"),
            ],
        )

        workouts = [
            ("trener1", "klijent1", "Trening A - noge", "2026-07-10", "completed"),
            ("trener1", "klijent1", "Trening B - gornji deo", "2026-07-16", "assigned"),
            ("trener1", "klijent3", "Kardio 1", "2026-07-01", "missed"),
            ("trener1", "klijent3", "Kardio 2", "2026-07-05", "missed"),
            ("trener2", "klijent4", "Mobilnost 1", "2026-07-15", "assigned"),
        ]
        for trainer_username, client_username, workout_name, date, status in workouts:
            connection.execute(
                """
                INSERT INTO workouts(trainer_id, client_id, name, scheduled_date, status)
                SELECT t.id, c.id, ?, ?, ? FROM users t, users c
                WHERE t.username=? AND c.username=?
                  AND NOT EXISTS (
                      SELECT 1 FROM workouts w
                      WHERE w.trainer_id=t.id AND w.client_id=c.id AND w.name=?
                  )
                """,
                (workout_name, date, status, trainer_username, client_username, workout_name),
            )

        workout_exercises = [
            ("Trening A - noge", "Cucanj", 1, 4, 10, None),
            ("Trening A - noge", "Iskorak", 2, 3, 12, None),
            ("Trening B - gornji deo", "Sklek", 1, 4, 12, None),
            ("Trening B - gornji deo", "Veslanje bucicama", 2, 4, 10, None),
            ("Kardio 1", "Plank", 1, 3, None, 2),
            ("Kardio 2", "Cucanj", 1, 3, 15, None),
            ("Mobilnost 1", "Plank", 1, 3, None, 2),
        ]
        for workout_name, exercise_name, order_no, sets, reps, duration in workout_exercises:
            connection.execute(
                """
                INSERT OR IGNORE INTO workout_exercises(
                    workout_id, exercise_id, exercise_order, sets,
                    repetitions, duration_minutes
                )
                SELECT w.id, e.id, ?, ?, ?, ? FROM workouts w, exercises e
                WHERE w.name=? AND e.name=?
                """,
                (order_no, sets, reps, duration, workout_name, exercise_name),
            )

        connection.execute(
            """
            INSERT OR IGNORE INTO workout_ratings(workout_id, client_id, rating, comment)
            SELECT w.id, c.id, 5, 'Odlican trening, intenzitet je bio taman.'
            FROM workouts w, users c
            WHERE w.name='Trening A - noge' AND c.username='klijent1'
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO exercise_ratings(workout_id, exercise_id, client_id, rating, comment)
            SELECT w.id, e.id, c.id, 4, 'Cucanj je dobar, ali je poslednja serija bila teska.'
            FROM workouts w, exercises e, users c
            WHERE w.name='Trening A - noge' AND e.name='Cucanj' AND c.username='klijent1'
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO trainer_ratings(client_id, trainer_id, rating, comment)
            SELECT c.id, t.id, 5, 'Strucan trener i veoma jasan program.'
            FROM users c, users t
            WHERE c.username='klijent1' AND t.username='trener1'
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO client_ratings(trainer_id, client_id, rating, comment)
            SELECT t.id, c.id, 4, 'Redovan, motivisan i dobro prihvata sugestije.'
            FROM users t, users c
            WHERE t.username='trener1' AND c.username='klijent1'
            """
        )

        connection.execute(
            """
            INSERT INTO payments(
                trainer_id, client_id, amount, status, paid_at, valid_until
            )
            SELECT t.id, c.id, 24000, 'paid',
                   '2026-07-01 10:00:00', '2026-08-01 10:00:00'
            FROM users t, users c
            WHERE t.username='trener1' AND c.username='klijent1'
              AND NOT EXISTS (
                  SELECT 1 FROM payments p
                  WHERE p.trainer_id=t.id AND p.client_id=c.id
                    AND p.paid_at='2026-07-01 10:00:00'
              )
            """
        )

        messages = [
            ("klijent1", "trener1", "Zdravo, poslao sam snimak cucnja. Mozes li da proveris tehniku?"),
            ("trener1", "klijent1", "Video je stigao. Obrati paznju da kolena prate pravac stopala."),
            ("klijent4", "trener2", "Da li mobilnost mogu da radim svako jutro?"),
            ("trener2", "klijent4", "Mozes, ali radi lagano i bez bola."),
        ]
        for sender, receiver, text in messages:
            connection.execute(
                """
                INSERT INTO messages(sender_id, receiver_id, text)
                SELECT s.id, r.id, ? FROM users s, users r
                WHERE s.username=? AND r.username=?
                  AND NOT EXISTS (
                      SELECT 1 FROM messages m
                      WHERE m.sender_id=s.id AND m.receiver_id=r.id AND m.text=?
                  )
                """,
                (text, sender, receiver, text),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
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
                diploma_license TEXT,
                biography TEXT,
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
                video_url TEXT,
                duration_minutes INTEGER CHECK (duration_minutes > 0),
                equipment_id INTEGER,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                scheduled_date TEXT,
                status TEXT NOT NULL DEFAULT 'assigned'
                    CHECK (status IN ('assigned', 'completed', 'missed')),
                FOREIGN KEY (trainer_id, client_id)
                    REFERENCES trainer_client_relations(trainer_id, client_id)
                    ON DELETE CASCADE
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

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                status TEXT NOT NULL DEFAULT 'paid'
                    CHECK (status IN ('paid', 'pending', 'failed')),
                paid_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                valid_until TEXT NOT NULL,
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

        connection.commit()
    finally:
        connection.close()
