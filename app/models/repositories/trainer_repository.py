from app.database import get_connection
from app.models.trainer_registration import TrainerRegistration


class TrainerRepository:
    """SQL upiti za pregled i odobravanje trenera."""

    def __init__(self, connection_factory=get_connection):
        self.connection_factory = connection_factory

    @staticmethod
    def _to_registration(row):
        return TrainerRegistration(
            user_id=row["user_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            education=row["education"] or "",
            years_of_experience=row["years_of_experience"],
            price_per_training=row["price_per_training"],
        )

    def list_pending_registrations(self):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """
                SELECT users.id AS user_id, users.username, users.first_name,
                       users.last_name, trainer_profiles.education,
                       trainer_profiles.years_of_experience,
                       trainer_profiles.price_per_training
                FROM users
                JOIN trainer_profiles ON trainer_profiles.user_id = users.id
                WHERE users.role = 'trainer'
                  AND users.registration_status = 'pending'
                ORDER BY users.created_at, users.id
                """
            ).fetchall()
            return [self._to_registration(row) for row in rows]
        finally:
            connection.close()

    def decide_registration(self, trainer_id, decision):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Odluka mora biti 'approved' ili 'rejected'.")

        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                UPDATE users
                SET registration_status = ?
                WHERE id = ?
                  AND role = 'trainer'
                  AND registration_status = 'pending'
                """,
                (decision, trainer_id),
            )
            connection.commit()
            return cursor.rowcount == 1
        finally:
            connection.close()

    def list_trainers_by_average_rating(self):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT users.id, users.username, users.first_name, users.last_name,
                       trainer_profiles.education,
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
                         rating_count DESC,
                         users.last_name,
                         users.first_name
                """
            ).fetchall()
        finally:
            connection.close()
