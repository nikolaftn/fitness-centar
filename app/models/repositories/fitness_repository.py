from app.database import get_connection


class FitnessRepository:
    """SQL operacije za klijent-trener tok, treninge, ocene, placanja i poruke."""

    def __init__(self, connection_factory=get_connection):
        self.connection_factory = connection_factory

    def list_available_trainers(self):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT users.id, users.username, users.first_name, users.last_name,
                       trainer_profiles.education,
                       trainer_profiles.years_of_experience,
                       trainer_profiles.price_per_training,
                       ROUND(AVG(trainer_ratings.rating), 2) AS average_rating,
                       COUNT(trainer_ratings.rating) AS rating_count
                FROM users
                JOIN trainer_profiles ON trainer_profiles.user_id = users.id
                LEFT JOIN trainer_ratings ON trainer_ratings.trainer_id = users.id
                WHERE users.role = 'trainer'
                  AND users.registration_status = 'approved'
                GROUP BY users.id
                ORDER BY average_rating IS NULL,
                         average_rating DESC,
                         users.last_name,
                         users.first_name
                """
            ).fetchall()
        finally:
            connection.close()

    def create_client_request(
        self,
        trainer_id,
        client_id,
        workouts_per_week,
        goals,
        height_cm,
        weight_kg,
        training_location,
        health_conditions,
    ):
        connection = self.connection_factory()
        try:
            profile = connection.execute(
                "SELECT price_per_training FROM trainer_profiles WHERE user_id = ?",
                (trainer_id,),
            ).fetchone()
            monthly_price = (
                profile["price_per_training"] * workouts_per_week * 4
                if profile is not None
                else 0
            )
            connection.execute(
                """
                INSERT INTO trainer_client_relations (
                    trainer_id, client_id, monthly_price, status,
                    workouts_per_week, goals, height_cm, weight_kg,
                    training_location, health_conditions
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                    monthly_price = excluded.monthly_price,
                    expiration_date = NULL,
                    status = 'pending',
                    workouts_per_week = excluded.workouts_per_week,
                    goals = excluded.goals,
                    height_cm = excluded.height_cm,
                    weight_kg = excluded.weight_kg,
                    training_location = excluded.training_location,
                    health_conditions = excluded.health_conditions
                """
                ,
                (
                    trainer_id,
                    client_id,
                    monthly_price,
                    workouts_per_week,
                    goals or None,
                    height_cm,
                    weight_kg,
                    training_location,
                    health_conditions or None,
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def list_client_relations(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT relations.*,
                       trainer.first_name || ' ' || trainer.last_name AS trainer_name,
                       trainer.username AS trainer_username
                FROM trainer_client_relations AS relations
                JOIN users AS trainer ON trainer.id = relations.trainer_id
                WHERE relations.client_id = ?
                ORDER BY relations.status = 'accepted' DESC,
                         trainer.last_name,
                         trainer.first_name
                """,
                (client_id,),
            ).fetchall()
        finally:
            connection.close()

    def list_trainer_requests(self, trainer_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT relations.*,
                       client.first_name || ' ' || client.last_name AS client_name,
                       client.username AS client_username
                FROM trainer_client_relations AS relations
                JOIN users AS client ON client.id = relations.client_id
                WHERE relations.trainer_id = ?
                ORDER BY relations.status = 'pending' DESC,
                         client.last_name,
                         client.first_name
                """,
                (trainer_id,),
            ).fetchall()
        finally:
            connection.close()

    def decide_client_request(self, trainer_id, client_id, status):
        if status not in {"accepted", "rejected"}:
            raise ValueError("Status mora biti accepted ili rejected.")
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                UPDATE trainer_client_relations
                SET status = ?
                WHERE trainer_id = ?
                  AND client_id = ?
                  AND status = 'pending'
                """,
                (status, trainer_id, client_id),
            )
            connection.commit()
            return cursor.rowcount == 1
        finally:
            connection.close()

    def list_accepted_clients(self, trainer_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT client.id, client.username,
                       client.first_name || ' ' || client.last_name AS client_name
                FROM trainer_client_relations AS relations
                JOIN users AS client ON client.id = relations.client_id
                WHERE relations.trainer_id = ?
                  AND relations.status = 'accepted'
                ORDER BY client.last_name, client.first_name
                """,
                (trainer_id,),
            ).fetchall()
        finally:
            connection.close()

    def list_exercises(self):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT id, name, description, video_url
                FROM exercises
                ORDER BY name
                """
            ).fetchall()
        finally:
            connection.close()

    def create_exercise(self, name, description, video_url):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO exercises (name, description, video_url)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    video_url = excluded.video_url
                """,
                (name, description or None, video_url or None),
            )
            connection.commit()
        finally:
            connection.close()

    def create_program_with_workout(
        self,
        trainer_id,
        client_id,
        program_name,
        workout_name,
        exercise_ids,
        scheduled_date=None,
    ):
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO programs (trainer_id, client_id, name, description)
                VALUES (?, ?, ?, NULL)
                """,
                (trainer_id, client_id, program_name),
            )
            program_id = cursor.lastrowid
            cursor = connection.execute(
                """
                INSERT INTO workouts (program_id, name, scheduled_date)
                VALUES (?, ?, ?)
                """,
                (program_id, workout_name, scheduled_date or None),
            )
            workout_id = cursor.lastrowid
            connection.executemany(
                """
                INSERT INTO workout_exercises (
                    workout_id, exercise_id, exercise_order
                ) VALUES (?, ?, ?)
                """,
                [
                    (workout_id, exercise_id, index)
                    for index, exercise_id in enumerate(exercise_ids, start=1)
                ],
            )
            connection.commit()
        finally:
            connection.close()

    def list_client_workouts(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT workouts.id, workouts.name, workouts.scheduled_date,
                       workouts.status, programs.name AS program_name,
                       trainer.id AS trainer_id,
                       trainer.first_name || ' ' || trainer.last_name AS trainer_name,
                       workout_ratings.rating AS workout_rating,
                       trainer_ratings.rating AS trainer_rating
                FROM workouts
                JOIN programs ON programs.id = workouts.program_id
                JOIN users AS trainer ON trainer.id = programs.trainer_id
                LEFT JOIN workout_ratings
                    ON workout_ratings.workout_id = workouts.id
                   AND workout_ratings.client_id = programs.client_id
                LEFT JOIN trainer_ratings
                    ON trainer_ratings.trainer_id = programs.trainer_id
                   AND trainer_ratings.client_id = programs.client_id
                WHERE programs.client_id = ?
                ORDER BY workouts.id DESC
                """,
                (client_id,),
            ).fetchall()
        finally:
            connection.close()

    def list_workout_exercises(self, workout_id, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT exercises.id, exercises.name, exercises.description,
                       exercises.video_url, workout_exercises.exercise_order,
                       exercise_ratings.rating,
                       exercise_ratings.comment,
                       (
                           SELECT video_url
                           FROM exercise_submissions
                           WHERE exercise_submissions.workout_id = workout_exercises.workout_id
                             AND exercise_submissions.exercise_id = workout_exercises.exercise_id
                             AND exercise_submissions.client_id = ?
                           ORDER BY exercise_submissions.created_at DESC
                           LIMIT 1
                       ) AS submitted_video
                FROM workout_exercises
                JOIN exercises ON exercises.id = workout_exercises.exercise_id
                LEFT JOIN exercise_ratings
                    ON exercise_ratings.workout_id = workout_exercises.workout_id
                   AND exercise_ratings.exercise_id = workout_exercises.exercise_id
                   AND exercise_ratings.client_id = ?
                WHERE workout_exercises.workout_id = ?
                ORDER BY workout_exercises.exercise_order
                """,
                (client_id, client_id, workout_id),
            ).fetchall()
        finally:
            connection.close()

    def rate_workout(self, workout_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO workout_ratings (workout_id, client_id, rating, comment)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(workout_id, client_id) DO UPDATE SET
                    rating = excluded.rating,
                    comment = excluded.comment,
                    created_at = CURRENT_TIMESTAMP
                """,
                (workout_id, client_id, rating, comment or None),
            )
            connection.execute(
                "UPDATE workouts SET status = 'completed' WHERE id = ?",
                (workout_id,),
            )
            connection.commit()
        finally:
            connection.close()

    def rate_trainer(self, trainer_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO trainer_ratings (client_id, trainer_id, rating, comment)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(client_id, trainer_id) DO UPDATE SET
                    rating = excluded.rating,
                    comment = excluded.comment,
                    created_at = CURRENT_TIMESTAMP
                """,
                (client_id, trainer_id, rating, comment or None),
            )
            connection.commit()
        finally:
            connection.close()

    def rate_exercise(self, workout_id, exercise_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO exercise_ratings (
                    workout_id, exercise_id, client_id, rating, comment
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(workout_id, exercise_id, client_id) DO UPDATE SET
                    rating = excluded.rating,
                    comment = excluded.comment,
                    created_at = CURRENT_TIMESTAMP
                """,
                (workout_id, exercise_id, client_id, rating, comment or None),
            )
            connection.commit()
        finally:
            connection.close()

    def submit_exercise_video(self, workout_id, exercise_id, client_id, video_url, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO exercise_submissions (
                    workout_id, exercise_id, client_id, video_url, comment
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (workout_id, exercise_id, client_id, video_url, comment or None),
            )
            connection.commit()
        finally:
            connection.close()

    def pay_monthly_subscription(self, trainer_id, client_id, period):
        connection = self.connection_factory()
        try:
            relation = connection.execute(
                """
                SELECT monthly_price
                FROM trainer_client_relations
                WHERE trainer_id = ?
                  AND client_id = ?
                  AND status = 'accepted'
                """,
                (trainer_id, client_id),
            ).fetchone()
            if relation is None:
                raise ValueError("Klijent nema prihvacen odnos sa trenerom.")
            connection.execute(
                """
                INSERT INTO payments (
                    trainer_id, client_id, amount, period, status
                ) VALUES (?, ?, ?, ?, 'paid')
                ON CONFLICT(trainer_id, client_id, period) DO UPDATE SET
                    amount = excluded.amount,
                    status = 'paid',
                    paid_at = CURRENT_TIMESTAMP
                """,
                (trainer_id, client_id, relation["monthly_price"], period),
            )
            connection.commit()
        finally:
            connection.close()

    def list_payments_for_client(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT payments.*, trainer.first_name || ' ' || trainer.last_name AS trainer_name
                FROM payments
                JOIN users AS trainer ON trainer.id = payments.trainer_id
                WHERE payments.client_id = ?
                ORDER BY payments.paid_at DESC
                """,
                (client_id,),
            ).fetchall()
        finally:
            connection.close()

    def send_message(self, sender_id, receiver_id, text):
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, text)
                VALUES (?, ?, ?)
                """,
                (sender_id, receiver_id, text),
            )
            connection.commit()
        finally:
            connection.close()

    def list_messages(self, user_id, other_user_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT messages.*, sender.username AS sender_username
                FROM messages
                JOIN users AS sender ON sender.id = messages.sender_id
                WHERE (sender_id = ? AND receiver_id = ?)
                   OR (sender_id = ? AND receiver_id = ?)
                ORDER BY messages.created_at, messages.id
                """,
                (user_id, other_user_id, other_user_id, user_id),
            ).fetchall()
        finally:
            connection.close()
