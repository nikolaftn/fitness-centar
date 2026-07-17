import sqlite3

from app.database import DATABASE_PATH


def create_schema(connection):
    connection.executescript(
        """
        CREATE TABLE users (
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

        CREATE TABLE trainer_profiles (
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

        CREATE TABLE trainer_client_relations (
            trainer_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            monthly_price REAL CHECK (monthly_price >= 0),
            expiration_date TEXT,
            is_paid INTEGER NOT NULL DEFAULT 0
                CHECK (is_paid IN (0, 1)),
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

        CREATE TABLE client_ratings (
            trainer_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (trainer_id, client_id),
            FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE trainer_ratings (
            client_id INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (client_id, trainer_id),
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL CHECK (category IN ('machine', 'prop')),
            description TEXT
        );

        CREATE TABLE exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            duration_minutes INTEGER CHECK (duration_minutes > 0),
            equipment_id INTEGER,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
        );

        CREATE TABLE workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'assigned'
                CHECK (status IN ('assigned', 'completed', 'missed')),
            FOREIGN KEY (trainer_id, client_id)
                REFERENCES trainer_client_relations(trainer_id, client_id)
                ON DELETE CASCADE
        );

        CREATE TABLE workout_exercises (
            workout_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            exercise_order INTEGER NOT NULL CHECK (exercise_order >= 1),
            sets INTEGER CHECK (sets > 0),
            repetitions INTEGER CHECK (repetitions > 0),
            duration_minutes INTEGER CHECK (duration_minutes > 0),
            completed INTEGER NOT NULL DEFAULT 0
                CHECK (completed IN (0, 1)),
            completed_at TEXT,
            PRIMARY KEY (workout_id, exercise_id),
            UNIQUE (workout_id, exercise_order),
            FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
        );

        CREATE TABLE workout_ratings (
            workout_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (workout_id, client_id),
            FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE exercise_ratings (
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

        CREATE TABLE payments (
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

        CREATE TABLE trainer_center_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK (amount >= 0),
            status TEXT NOT NULL DEFAULT 'paid'
                CHECK (status IN ('paid', 'pending', 'failed')),
            paid_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            valid_until TEXT NOT NULL,
            FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
            payment_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL
                CHECK (notification_type IN ('expiring', 'expired')),
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0
                CHECK (is_read IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (payment_id, notification_type),
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
        );

        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'text'
                CHECK (message_type IN ('text', 'workout_rating', 'exercise_rating')),
            rating_key TEXT UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )


def insert_test_data(connection):
    connection.executescript(
        """
        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('admin', 'admin', 'Glavni', 'Administrator', '1980-01-01', 'admin123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trener1', 'trainer', 'Marko', 'Markovic', '1988-05-14', 'trener123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trener2', 'trainer', 'Ana', 'Anic', '1992-09-22', 'trener123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trener_pending', 'trainer', 'Nikola', 'Nikolic', '1995-02-18', 'trener123', 'pending');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trener_rejected', 'trainer', 'Milan', 'Milic', '1990-07-11', 'trener123', 'rejected');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('klijent1', 'client', 'Petar', 'Petrovic', '2001-03-10', 'klijent123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('klijent2', 'client', 'Jelena', 'Jovanovic', '1999-11-08', 'klijent123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('klijent3', 'client', 'Luka', 'Lukic', '2002-06-15', 'klijent123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('klijent4', 'client', 'Sara', 'Saric', '2000-12-03', 'klijent123', 'approved');

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (2, 'Fakultet sporta i fizickog vaspitanja', 'FIT-2020-001', 'Trener snage i kondicije.', 8, 2000.0);

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (3, 'Visoka sportska skola', 'LIC-2022-114', 'Pilates, mobilnost i funkcionalni trening.', 4, 1500.0);

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (4, 'Fakultet sporta', 'CEKA-PROVERU', 'Zahtev ceka odobrenje administratora.', 2, 1200.0);

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (5, 'Kurs fitnes instruktora', 'ODBIJENA-LICENCA', 'Primer odbijenog zahteva.', 1, 1000.0);

        INSERT INTO equipment (name, category, description)
        VALUES ('Traka za trcanje', 'machine', 'Kardio sprava sa podesavanjem brzine.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Leg press', 'machine', 'Sprava za trening nogu.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Lat masina', 'machine', 'Sprava za ledja.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Bucice', 'prop', 'Par bucica razlicitih tezina.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Prostirka', 'prop', 'Prostirka za vezbe na podu.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Elasticna traka', 'prop', 'Rekvizit za aktivaciju i mobilnost.');

        INSERT INTO exercises (name, description, duration_minutes, equipment_id)
        VALUES ('Cucanj', 'Osnovna vezba za noge i gluteus.', 10, 6);

        INSERT INTO exercises (name, description, duration_minutes, equipment_id)
        VALUES ('Sklek', 'Vezba za grudi, ramena i triceps.', 8, 5);

        INSERT INTO exercises (name, description, duration_minutes, equipment_id)
        VALUES ('Plank', 'Staticka vezba za stabilizaciju trupa.', 5, 5);

        INSERT INTO exercises (name, description, duration_minutes, equipment_id)
        VALUES ('Iskorak', 'Jednonozna vezba za noge i ravnotezu.', 10, 4);

        INSERT INTO exercises (name, description, duration_minutes, equipment_id)
        VALUES ('Veslanje bucicama', 'Vezba za ledja uz bucice.', 12, 4);

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (2, 6, 24000.0, '2026-08-01 10:00:00', 1, 'accepted', 3, 'Povecanje snage i misicne mase', 182, 82, 'gym', 'Nema');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (2, 7, 16000.0, NULL, 0, 'pending', 2, 'Mrsavljenje 6 kg', 168, 73, 'both', 'Povremeni bol u kolenu');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (2, 8, 16000.0, '2026-08-01 10:00:00', 1, 'accepted', 2, 'Bolja kondicija', 178, 91, 'gym', 'Nema');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (3, 9, 12000.0, '2026-07-19 00:00:00', 1, 'accepted', 2, 'Mobilnost i drzanje', 165, 58, 'home', 'Blaga skolioza');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (3, 7, 6000.0, '2026-07-01 10:00:00', 0, 'expired', 1, 'Pocetnicki program', 170, 65, 'home', 'Nema');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 6, 'Trening A - noge', '2026-07-10', 'completed');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 6, 'Trening B - gornji deo', '2026-07-16', 'assigned');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 8, 'Kardio 1', '2026-07-01', 'missed');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 8, 'Kardio 2', '2026-07-05', 'missed');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (3, 9, 'Mobilnost 1', '2026-07-18', 'assigned');

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes, completed, completed_at)
        VALUES (1, 1, 1, 4, 10, NULL, 1, '2026-07-10 18:00:00');

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes, completed, completed_at)
        VALUES (1, 4, 2, 3, 12, NULL, 1, '2026-07-10 18:00:00');

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (2, 2, 1, 4, 12, NULL);

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (2, 5, 2, 4, 10, NULL);

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (3, 3, 1, 3, NULL, 2);

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (4, 1, 1, 3, 15, NULL);

        INSERT INTO workout_exercises (workout_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (5, 3, 1, 3, NULL, 2);

        INSERT INTO workout_ratings (workout_id, client_id, rating, comment)
        VALUES (1, 6, 5, 'Odlican trening, intenzitet je bio taman.');

        INSERT INTO exercise_ratings (workout_id, exercise_id, client_id, rating, comment)
        VALUES (1, 1, 6, 4, 'Cucanj je dobar, ali je poslednja serija bila teska.');

        INSERT INTO trainer_ratings (client_id, trainer_id, rating, comment)
        VALUES (6, 2, 5, 'Strucan trener i veoma jasan program.');

        INSERT INTO client_ratings (trainer_id, client_id, rating, comment)
        VALUES (2, 6, 4, 'Redovan, motivisan i dobro prihvata sugestije.');

        INSERT INTO client_ratings (trainer_id, client_id, rating, comment)
        VALUES (3, 7, 3, 'Korektna saradnja, ali je potrebno vise kontinuiteta.');

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (2, 6, 24000, 'paid', '2026-07-01 10:00:00', '2026-08-01 10:00:00');

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (2, 8, 16000, 'paid', '2026-07-01 10:00:00', '2026-08-01 10:00:00');

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (3, 9, 12000, 'paid', '2026-06-19 00:00:00', '2026-07-19 00:00:00');

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (3, 7, 6000, 'paid', '2026-06-01 10:00:00', '2026-07-01 10:00:00');

        INSERT INTO trainer_center_payments
            (trainer_id, amount, status, paid_at, valid_until)
        VALUES
            (2, 30000, 'paid', datetime('now', '-5 days'), datetime('now', '+25 days'));

        INSERT INTO trainer_center_payments
            (trainer_id, amount, status, paid_at, valid_until)
        VALUES
            (3, 30000, 'paid', datetime('now', '-1 month', '-1 day'), datetime('now', '-1 day'));

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (6, 2, 'Zdravo, mozes li da mi objasnis pravilnu tehniku cucnja?');

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (2, 6, 'Naravno. Obrati paznju da kolena prate pravac stopala.');

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (9, 3, 'Da li mobilnost mogu da radim svako jutro?');

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (3, 9, 'Mozes, ali radi lagano i bez bola.');

        INSERT INTO messages (sender_id, receiver_id, text, message_type, rating_key)
        VALUES (6, 2, 'OCENA TRENINGA\nTrening: Trening A - noge\nOcena: 5/5\nKomentar: Odlican trening, intenzitet je bio taman.', 'workout_rating', 'workout_rating:1:6');

        INSERT INTO messages (sender_id, receiver_id, text, message_type, rating_key)
        VALUES (6, 2, 'OCENA VEZBE\nTrening: Trening A - noge\nVezba: Cucanj\nOcena: 4/5\nKomentar: Cucanj je dobar, ali je poslednja serija bila teska.', 'exercise_rating', 'exercise_rating:1:1:6');
        """
    )


def main():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        create_schema(connection)
        insert_test_data(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        connection.close()
        if DATABASE_PATH.exists():
            DATABASE_PATH.unlink()
        raise
    else:
        connection.close()

    print(f"Test baza je ponovo napravljena: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
