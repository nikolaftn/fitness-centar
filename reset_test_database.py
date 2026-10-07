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
            trainer_id INTEGER NOT NULL,
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            duration_minutes INTEGER CHECK (duration_minutes > 0),
            equipment_id INTEGER,
            PRIMARY KEY (trainer_id, id),
            UNIQUE (trainer_id, name),
            FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE,
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
            UNIQUE (id, trainer_id),
            FOREIGN KEY (trainer_id, client_id)
                REFERENCES trainer_client_relations(trainer_id, client_id)
                ON DELETE CASCADE
        );

        CREATE TABLE workout_exercises (
            workout_id INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            exercise_order INTEGER NOT NULL CHECK (exercise_order >= 1),
            sets INTEGER NOT NULL CHECK (sets > 0),
            repetitions INTEGER NOT NULL CHECK (repetitions > 0),
            duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
            completed INTEGER NOT NULL DEFAULT 0
                CHECK (completed IN (0, 1)),
            completed_at TEXT,
            PRIMARY KEY (workout_id, exercise_id),
            UNIQUE (workout_id, exercise_order),
            FOREIGN KEY (workout_id, trainer_id)
                REFERENCES workouts(id, trainer_id) ON DELETE CASCADE,
            FOREIGN KEY (trainer_id, exercise_id)
                REFERENCES exercises(trainer_id, id) ON DELETE CASCADE
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
        VALUES ('admin', 'admin', 'Main', 'Administrator', '1980-01-01', 'admin123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trainer1', 'trainer', 'Marko', 'Markovic', '1988-05-14', 'trainer123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trainer2', 'trainer', 'Ana', 'Anic', '1992-09-22', 'trainer123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trainer_pending', 'trainer', 'Nikola', 'Nikolic', '1995-02-18', 'trainer123', 'pending');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('trainer_rejected', 'trainer', 'Milan', 'Milic', '1990-07-11', 'trainer123', 'rejected');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('client1', 'client', 'Petar', 'Petrovic', '2001-03-10', 'client123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('client2', 'client', 'Jelena', 'Jovanovic', '1999-11-08', 'client123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('client3', 'client', 'Luka', 'Lukic', '2002-06-15', 'client123', 'approved');

        INSERT INTO users (username, role, first_name, last_name, birth_date, password, registration_status)
        VALUES ('client4', 'client', 'Sara', 'Saric', '2000-12-03', 'client123', 'approved');

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (2, 'Faculty of Sport and Physical Education', 'FIT-2020-001', 'Strength and conditioning trainer.', 8, 2000.0);

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (3, 'Higher School of Sports', 'LIC-2022-114', 'Pilates, mobility, and functional training.', 4, 1500.0);

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (4, 'Faculty of Sports', 'PENDING-REVIEW', 'Request awaiting administrator approval.', 2, 1200.0);

        INSERT INTO trainer_profiles (user_id, education, diploma_license, biography, years_of_experience, price_per_training)
        VALUES (5, 'Fitness instructor course', 'REJECTED-LICENSE', 'Example of a rejected request.', 1, 1000.0);

        INSERT INTO equipment (name, category, description)
        VALUES ('Treadmill', 'machine', 'Cardio machine with adjustable speed.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Leg press', 'machine', 'Machine for leg workouts.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Lat pulldown machine', 'machine', 'Back exercise machine.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Dumbbells', 'prop', 'A pair of dumbbells of different weights.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Exercise mat', 'prop', 'Mat for floor exercises.');

        INSERT INTO equipment (name, category, description)
        VALUES ('Resistance band', 'prop', 'Equipment for activation and mobility.');

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (2, 1, 'Squat', 'A basic exercise for the legs and glutes.', 10, 6);

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (2, 2, 'Push-up', 'Exercise for the chest, shoulders, and triceps.', 8, 5);

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (2, 3, 'Plank', 'Static exercise for core stability.', 5, 5);

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (2, 4, 'Lunge', 'Single-leg exercise for the legs and balance.', 10, 4);

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (2, 5, 'Dumbbell row', 'Back exercise using dumbbells.', 12, 4);

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (3, 1, 'Plank', 'Core stability for a mobility program.', 5, 5);

        INSERT INTO exercises (trainer_id, id, name, description, duration_minutes, equipment_id)
        VALUES (3, 2, 'Morning mobility', 'Gentle full-body mobility exercise.', 12, 5);

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (2, 6, 24000.0, datetime('now', '+30 days'), 1, 'accepted', 3, 'Increase strength and muscle mass', 182, 82, 'gym', 'None');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (2, 7, 16000.0, NULL, 0, 'pending', 2, 'Lose 6 kg', 168, 73, 'both', 'Occasional knee pain');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (2, 8, 16000.0, datetime('now', '+30 days'), 1, 'accepted', 2, 'Improved fitness', 178, 91, 'gym', 'None');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (3, 9, 12000.0, datetime('now', '+30 days'), 1, 'accepted', 2, 'Mobility and posture', 165, 58, 'home', 'Mild scoliosis');

        INSERT INTO trainer_client_relations (trainer_id, client_id, monthly_price, expiration_date, is_paid, status, workouts_per_week, goals, height_cm, weight_kg, training_location, health_conditions)
        VALUES (3, 7, 6000.0, '2026-07-01 10:00:00', 0, 'expired', 1, 'Beginner program', 170, 65, 'home', 'None');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 6, 'Workout A - Legs', '2026-07-10', 'completed');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 6, 'Workout B - Upper Body', date('now', '+7 days'), 'assigned');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 8, 'Cardio 1', '2026-07-01', 'missed');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (2, 8, 'Cardio 2', '2026-07-05', 'missed');

        INSERT INTO workouts (trainer_id, client_id, name, scheduled_date, status)
        VALUES (3, 9, 'Mobility 1', date('now', '+5 days'), 'assigned');

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes, completed, completed_at)
        VALUES (1, 2, 1, 1, 4, 10, 10, 1, '2026-07-10 18:00:00');

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes, completed, completed_at)
        VALUES (1, 2, 4, 2, 3, 12, 10, 1, '2026-07-10 18:00:00');

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (2, 2, 2, 1, 4, 12, 8);

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (2, 2, 5, 2, 4, 10, 12);

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (3, 2, 3, 1, 3, 1, 2);

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (4, 2, 1, 1, 3, 15, 10);

        INSERT INTO workout_exercises (workout_id, trainer_id, exercise_id, exercise_order, sets, repetitions, duration_minutes)
        VALUES (5, 3, 1, 1, 3, 1, 2);

        INSERT INTO workout_ratings (workout_id, client_id, rating, comment)
        VALUES (1, 6, 5, 'Excellent workout; the intensity was just right.');

        INSERT INTO exercise_ratings (workout_id, exercise_id, client_id, rating, comment)
        VALUES (1, 1, 6, 4, 'The squat is good, but the last set was difficult.');

        INSERT INTO trainer_ratings (client_id, trainer_id, rating, comment)
        VALUES (6, 2, 5, 'Knowledgeable trainer and a very clear program.');

        INSERT INTO client_ratings (trainer_id, client_id, rating, comment)
        VALUES (2, 6, 4, 'Consistent, motivated, and receptive to feedback.');

        INSERT INTO client_ratings (trainer_id, client_id, rating, comment)
        VALUES (3, 7, 3, 'Good collaboration, but more consistency is needed.');

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (2, 6, 24000, 'paid', datetime('now'), datetime('now', '+30 days'));

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (2, 8, 16000, 'paid', datetime('now'), datetime('now', '+30 days'));

        INSERT INTO payments (trainer_id, client_id, amount, status, paid_at, valid_until)
        VALUES (3, 9, 12000, 'paid', datetime('now'), datetime('now', '+30 days'));

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
        VALUES (6, 2, 'Hi, can you explain the correct squat technique?');

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (2, 6, 'Of course. Make sure your knees follow the direction of your toes.');

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (9, 3, 'Can I do mobility exercises every morning?');

        INSERT INTO messages (sender_id, receiver_id, text)
        VALUES (3, 9, 'Yes, but keep it light and stop if you feel pain.');

        INSERT INTO messages (sender_id, receiver_id, text, message_type, rating_key)
        VALUES (6, 2, 'WORKOUT RATING\nWorkout: Workout A - Legs\nRating: 5/5\nComment: Excellent workout; the intensity was just right.', 'workout_rating', 'workout_rating:1:6');

        INSERT INTO messages (sender_id, receiver_id, text, message_type, rating_key)
        VALUES (6, 2, 'EXERCISE RATING\nWorkout: Workout A - Legs\nExercise: Squat\nRating: 4/5\nComment: The squat is good, but the last set was difficult.', 'exercise_rating', 'exercise_rating:1:1:6');
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

    print(f"Test database recreated: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
