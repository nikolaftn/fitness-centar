from app.database import get_connection
from app.models.domain.fitness_entities import (
    Equipment,
    Exercise,
    Notification,
    TrainerClientRelation,
    Workout,
)


class FitnessRepository:
    """SQL operacije za kompletan tok klijenta i trenera."""

    def __init__(self, connection_factory=get_connection):
        self.connection_factory = connection_factory

    @staticmethod
    def _to_exercise(row):
        return Exercise(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            duration_minutes=row["duration_minutes"],
            equipment_id=row["equipment_id"],
            equipment_name=row["equipment_name"],
            exercise_order=row["exercise_order"] if "exercise_order" in row.keys() else None,
            rating=row["rating"] if "rating" in row.keys() else None,
            comment=row["comment"] if "comment" in row.keys() else None,
            completed=bool(row["completed"]) if "completed" in row.keys() else False,
        )

    @staticmethod
    def _to_equipment(row):
        return Equipment(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            description=row["description"],
        )

    @staticmethod
    def _to_workout(row, client_id=None):
        return Workout(
            id=row["id"],
            name=row["name"],
            scheduled_date=row["scheduled_date"],
            status=row["status"],
            trainer_id=row["trainer_id"] if "trainer_id" in row.keys() else None,
            client_id=client_id if client_id is not None else row["client_id"],
            trainer_name=row["trainer_name"] if "trainer_name" in row.keys() else None,
            client_name=row["client_name"] if "client_name" in row.keys() else None,
            workout_rating=row["workout_rating"] if "workout_rating" in row.keys() else None,
            trainer_rating=row["trainer_rating"] if "trainer_rating" in row.keys() else None,
        )

    @staticmethod
    def _to_relation(row):
        return TrainerClientRelation(
            trainer_id=row["trainer_id"],
            client_id=row["client_id"],
            status=row["status"],
            monthly_price=row["monthly_price"],
            expiration_date=row["expiration_date"],
            workouts_per_week=row["workouts_per_week"],
            goals=row["goals"],
            height_cm=row["height_cm"],
            weight_kg=row["weight_kg"],
            training_location=row["training_location"],
            health_conditions=row["health_conditions"],
            is_paid=bool(row["is_paid"]),
            trainer_name=row["trainer_name"] if "trainer_name" in row.keys() else None,
            client_name=row["client_name"] if "client_name" in row.keys() else None,
        )

    @staticmethod
    def _to_notification(row):
        return Notification(
            id=row["id"],
            client_id=row["client_id"],
            trainer_id=row["trainer_id"],
            payment_id=row["payment_id"],
            notification_type=row["notification_type"],
            message=row["message"],
            is_read=bool(row["is_read"]),
            created_at=row["created_at"],
        )

    # ------------------------- TRENERI I ODNOSI -------------------------
    def list_available_trainers(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT u.id, u.username, u.first_name, u.last_name,
                       tp.education, tp.diploma_license, tp.biography,
                       tp.years_of_experience, tp.price_per_training,
                       ROUND(AVG(tr.rating), 2) AS average_rating,
                       COUNT(tr.rating) AS rating_count
                FROM users u
                JOIN trainer_profiles tp ON tp.user_id = u.id
                LEFT JOIN trainer_ratings tr ON tr.trainer_id = u.id
                WHERE u.role = 'trainer'
                  AND u.registration_status = 'approved'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM trainer_client_relations r
                      WHERE r.trainer_id = u.id
                        AND r.client_id = ?
                        AND r.status IN ('pending', 'accepted')
                  )
                GROUP BY u.id
                ORDER BY average_rating IS NULL, average_rating DESC,
                         u.last_name, u.first_name
                """,
                (client_id,),
            ).fetchall()
        finally:
            connection.close()

    def get_trainer_profile(self, trainer_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT u.first_name, u.last_name, u.birth_date,
                       tp.education, tp.diploma_license, tp.biography,
                       tp.years_of_experience, tp.price_per_training
                FROM users u
                JOIN trainer_profiles tp ON tp.user_id = u.id
                WHERE u.id = ?
                """,
                (trainer_id,),
            ).fetchone()
        finally:
            connection.close()

    def update_trainer_profile(self, trainer_id, data):
        connection = self.connection_factory()
        try:
            connection.execute(
                """UPDATE users SET first_name=?, last_name=?, birth_date=? WHERE id=?""",
                (data["first_name"], data["last_name"], data["birth_date"], trainer_id),
            )
            connection.execute(
                """
                UPDATE trainer_profiles
                SET education=?, diploma_license=?, biography=?,
                    years_of_experience=?, price_per_training=?
                WHERE user_id=?
                """,
                (
                    data["education"] or None,
                    data["diploma_license"] or None,
                    data["biography"] or None,
                    data["years_of_experience"],
                    data["price_per_training"],
                    trainer_id,
                ),
            )
            connection.execute(
                """
                UPDATE trainer_client_relations
                SET monthly_price = workouts_per_week * ? * 4
                WHERE trainer_id=? AND status='accepted'
                """,
                (data["price_per_training"], trainer_id),
            )
            connection.commit()
        finally:
            connection.close()

    def get_trainer_price(self, trainer_id):
        connection = self.connection_factory()
        try:
            profile = connection.execute(
                "SELECT price_per_training FROM trainer_profiles WHERE user_id=?",
                (trainer_id,),
            ).fetchone()
            return None if profile is None else profile["price_per_training"]
        finally:
            connection.close()

    def create_client_request(self, trainer_id, client_id, workouts_per_week,
                              goals, height_cm, weight_kg, training_location,
                              health_conditions, monthly_price):
        connection = self.connection_factory()
        try:
            existing_relation = connection.execute(
                """SELECT status FROM trainer_client_relations
                   WHERE trainer_id=? AND client_id=?""",
                (trainer_id, client_id),
            ).fetchone()
            if existing_relation and existing_relation["status"] == "pending":
                raise ValueError("Zahtev ovom treneru je vec poslat.")
            if existing_relation and existing_relation["status"] == "accepted":
                raise ValueError("Vec imate prihvacen odnos sa ovim trenerom.")

            connection.execute(
                """
                INSERT INTO trainer_client_relations(
                    trainer_id, client_id, monthly_price, status,
                    workouts_per_week, goals, height_cm, weight_kg,
                    training_location, health_conditions
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                    monthly_price=excluded.monthly_price,
                    expiration_date=NULL, is_paid=0, status='pending',
                    workouts_per_week=excluded.workouts_per_week,
                    goals=excluded.goals, height_cm=excluded.height_cm,
                    weight_kg=excluded.weight_kg,
                    training_location=excluded.training_location,
                    health_conditions=excluded.health_conditions
                """,
                (trainer_id, client_id, monthly_price, workouts_per_week,
                 goals or None, height_cm, weight_kg, training_location,
                 health_conditions or None),
            )
            connection.commit()
        finally:
            connection.close()

    def list_client_relations(self, client_id):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """
                SELECT r.*, u.first_name || ' ' || u.last_name AS trainer_name,
                       u.username AS trainer_username
                FROM trainer_client_relations r
                JOIN users u ON u.id=r.trainer_id
                WHERE r.client_id=? AND r.status IN ('pending', 'accepted')
                ORDER BY r.status='accepted' DESC, u.last_name, u.first_name
                """, (client_id,)
            ).fetchall()
            return [self._to_relation(row) for row in rows]
        finally:
            connection.close()

    def list_trainer_requests(self, trainer_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT r.*, u.first_name || ' ' || u.last_name AS client_name,
                       u.username AS client_username
                FROM trainer_client_relations r
                JOIN users u ON u.id=r.client_id
                WHERE r.trainer_id=? AND r.status='pending'
                ORDER BY u.last_name, u.first_name
                """, (trainer_id,)
            ).fetchall()
        finally:
            connection.close()

    def decide_client_request(self, trainer_id, client_id, status):
        if status not in {"accepted", "rejected"}:
            raise ValueError("Neispravan status.")
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """UPDATE trainer_client_relations
                   SET status=?, is_paid=0, expiration_date=NULL
                   WHERE trainer_id=? AND client_id=? AND status='pending'""",
                (status, trainer_id, client_id),
            )
            connection.commit()
            return cursor.rowcount == 1
        finally:
            connection.close()

    def list_accepted_clients(self, trainer_id):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """
                SELECT u.id, u.username,
                       u.first_name || ' ' || u.last_name AS client_name,
                       r.workouts_per_week, r.monthly_price, r.goals,
                       r.height_cm, r.weight_kg, r.training_location,
                       r.health_conditions
                FROM trainer_client_relations r
                JOIN users u ON u.id=r.client_id
                WHERE r.trainer_id=? AND r.status='accepted' AND r.is_paid=1
                ORDER BY u.last_name, u.first_name
                """, (trainer_id,)
            ).fetchall()
            clients = []
            for row in rows:
                client = dict(row)
                payment = connection.execute(
                    """SELECT paid_at, valid_until
                       FROM payments
                       WHERE trainer_id=? AND client_id=? AND status='paid'
                         AND paid_at <= CURRENT_TIMESTAMP
                         AND valid_until > CURRENT_TIMESTAMP
                       ORDER BY valid_until DESC
                       LIMIT 1""",
                    (trainer_id, row["id"]),
                ).fetchone()
                if payment is None:
                    continue
                client["active_until"] = payment["valid_until"]
                missed = connection.execute(
                    """SELECT COUNT(*) AS total
                       FROM workouts
                       WHERE trainer_id=? AND client_id=? AND status='missed'
                         AND date(scheduled_date) >= date(?)
                         AND date(scheduled_date) < date(?)""",
                    (
                        trainer_id,
                        row["id"],
                        payment["paid_at"],
                        payment["valid_until"],
                    ),
                ).fetchone()
                client["missed_count"] = missed["total"]
                clients.append(client)
            return clients
        finally:
            connection.close()

    # ------------------------------ VEZBE ------------------------------
    def list_exercises(self):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """SELECT e.id, e.name, e.description, e.duration_minutes,
                          e.equipment_id,
                          q.name AS equipment_name
                   FROM exercises e
                   LEFT JOIN equipment q ON q.id = e.equipment_id
                   ORDER BY e.name"""
            ).fetchall()
            return [self._to_exercise(row) for row in rows]
        finally:
            connection.close()

    def save_exercise(self, exercise_id, name, description, duration_minutes,
                      equipment_id):
        connection = self.connection_factory()
        try:
            if exercise_id:
                connection.execute(
                    """UPDATE exercises SET name=?, description=?,
                       duration_minutes=?, equipment_id=? WHERE id=?""",
                    (name, description or None, duration_minutes, equipment_id,
                     exercise_id),
                )
            else:
                connection.execute(
                    """INSERT INTO exercises(
                           name, description, duration_minutes, equipment_id
                       ) VALUES (?, ?, ?, ?)""",
                    (name, description or None, duration_minutes, equipment_id),
                )
            connection.commit()
        finally:
            connection.close()

    def create_exercise(self, name, description):
        self.save_exercise(None, name, description, None, None)

    def delete_exercise(self, exercise_id):
        connection = self.connection_factory()
        try:
            connection.execute("DELETE FROM exercises WHERE id=?", (exercise_id,))
            connection.commit()
        finally:
            connection.close()

    # ------------------------------ OPREMA ------------------------------
    def list_equipment(self):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                "SELECT id, name, category, description FROM equipment ORDER BY name"
            ).fetchall()
            return [self._to_equipment(row) for row in rows]
        finally:
            connection.close()

    def save_equipment(self, equipment_id, name, category, description):
        connection = self.connection_factory()
        try:
            if equipment_id:
                connection.execute(
                    "UPDATE equipment SET name=?, category=?, description=? WHERE id=?",
                    (name, category, description or None, equipment_id),
                )
            else:
                connection.execute(
                    "INSERT INTO equipment(name, category, description) VALUES (?, ?, ?)",
                    (name, category, description or None),
                )
            connection.commit()
        finally:
            connection.close()

    def delete_equipment(self, equipment_id):
        connection = self.connection_factory()
        try:
            connection.execute("DELETE FROM equipment WHERE id=?", (equipment_id,))
            connection.commit()
        finally:
            connection.close()

    # ------------------------------ TRENINZI ----------------------------
    def mark_overdue_workouts(self):
        connection = self.connection_factory()
        try:
            connection.execute(
                """UPDATE workouts
                   SET status='missed'
                   WHERE status='assigned'
                     AND scheduled_date IS NOT NULL
                     AND date(scheduled_date) < date('now', 'localtime')"""
            )
            connection.commit()
        finally:
            connection.close()

    def get_active_membership_expiration(self, trainer_id, client_id):
        connection = self.connection_factory()
        try:
            payment = connection.execute(
                """SELECT p.valid_until
                   FROM payments p
                   JOIN trainer_client_relations r
                     ON r.trainer_id=p.trainer_id AND r.client_id=p.client_id
                   WHERE p.trainer_id=? AND p.client_id=?
                     AND r.status='accepted' AND r.is_paid=1 AND p.status='paid'
                     AND p.paid_at <= CURRENT_TIMESTAMP
                     AND p.valid_until > CURRENT_TIMESTAMP
                   ORDER BY p.valid_until DESC
                   LIMIT 1""",
                (trainer_id, client_id),
            ).fetchone()
            return payment["valid_until"] if payment else None
        finally:
            connection.close()

    def count_missed_workouts_in_active_membership(self, trainer_id, client_id):
        connection = self.connection_factory()
        try:
            payment = connection.execute(
                """SELECT paid_at, valid_until
                   FROM payments
                   WHERE trainer_id=? AND client_id=? AND status='paid'
                     AND paid_at <= CURRENT_TIMESTAMP
                     AND valid_until > CURRENT_TIMESTAMP
                   ORDER BY valid_until DESC
                   LIMIT 1""",
                (trainer_id, client_id),
            ).fetchone()
            if payment is None:
                return 0
            row = connection.execute(
                """SELECT COUNT(*) AS total
                   FROM workouts
                   WHERE trainer_id=? AND client_id=? AND status='missed'
                     AND date(scheduled_date) >= date(?)
                     AND date(scheduled_date) < date(?)""",
                (
                    trainer_id,
                    client_id,
                    payment["paid_at"],
                    payment["valid_until"],
                ),
            ).fetchone()
            return row["total"]
        finally:
            connection.close()

    def create_workout(self, trainer_id, client_id, workout_name, exercise_ids,
                       scheduled_date):
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """INSERT INTO workouts(trainer_id, client_id, name, scheduled_date)
                   VALUES (?, ?, ?, ?)""",
                (trainer_id, client_id, workout_name, scheduled_date),
            )
            workout_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO workout_exercises(workout_id, exercise_id, exercise_order) VALUES (?, ?, ?)",
                [(workout_id, ex_id, index) for index, ex_id in enumerate(exercise_ids, 1)],
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list_client_workouts(self, client_id, trainer_id):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """
                SELECT w.id, w.name, w.scheduled_date, w.status,
                       t.id AS trainer_id,
                       t.first_name || ' ' || t.last_name AS trainer_name,
                       wr.rating AS workout_rating, tr.rating AS trainer_rating
                FROM workouts w
                JOIN users t ON t.id=w.trainer_id
                LEFT JOIN workout_ratings wr ON wr.workout_id=w.id AND wr.client_id=w.client_id
                LEFT JOIN trainer_ratings tr ON tr.trainer_id=w.trainer_id AND tr.client_id=w.client_id
                WHERE w.client_id=? AND w.trainer_id=?
                ORDER BY w.id DESC
                """, (client_id, trainer_id)
            ).fetchall()
            return [self._to_workout(row, client_id) for row in rows]
        finally:
            connection.close()

    def list_workout_exercises(self, workout_id, client_id):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """
                SELECT e.id, e.name, e.description, e.equipment_id,
                       q.name AS equipment_name,
                       COALESCE(we.duration_minutes, e.duration_minutes) AS duration_minutes,
                       we.exercise_order, we.completed, er.rating, er.comment
                FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id
                LEFT JOIN equipment q ON q.id=e.equipment_id
                LEFT JOIN exercise_ratings er ON er.workout_id=we.workout_id
                  AND er.exercise_id=we.exercise_id AND er.client_id=?
                WHERE we.workout_id=? ORDER BY we.exercise_order
                """, (client_id, workout_id)
            ).fetchall()
            return [self._to_exercise(row) for row in rows]
        finally:
            connection.close()

    def get_client_workout(self, workout_id, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """SELECT id, trainer_id, client_id, name, scheduled_date, status
                   FROM workouts
                   WHERE id=? AND client_id=?""",
                (workout_id, client_id),
            ).fetchone()
        finally:
            connection.close()

    def set_workout_exercise_completed(
        self, workout_id, exercise_id, client_id, completed
    ):
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """UPDATE workout_exercises
                   SET completed=?,
                       completed_at=CASE WHEN ?=1 THEN CURRENT_TIMESTAMP ELSE NULL END
                   WHERE workout_id=? AND exercise_id=?
                     AND EXISTS (
                         SELECT 1 FROM workouts
                         WHERE id=? AND client_id=?
                     )""",
                (
                    int(completed),
                    int(completed),
                    workout_id,
                    exercise_id,
                    workout_id,
                    client_id,
                ),
            )
            connection.commit()
            if cursor.rowcount != 1:
                raise ValueError("Vezba nije pronadjena u ovom treningu.")
        finally:
            connection.close()

    def is_workout_exercise_completed(self, workout_id, exercise_id):
        connection = self.connection_factory()
        try:
            row = connection.execute(
                """SELECT completed FROM workout_exercises
                   WHERE workout_id=? AND exercise_id=?""",
                (workout_id, exercise_id),
            ).fetchone()
            return bool(row["completed"]) if row else False
        finally:
            connection.close()

    def all_workout_exercises_completed(self, workout_id):
        connection = self.connection_factory()
        try:
            row = connection.execute(
                """SELECT COUNT(*) AS total,
                          SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) AS completed
                   FROM workout_exercises
                   WHERE workout_id=?""",
                (workout_id,),
            ).fetchone()
            return row["total"] > 0 and row["total"] == row["completed"]
        finally:
            connection.close()

    def rate_workout(self, workout_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """INSERT INTO workout_ratings(workout_id, client_id, rating, comment)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(workout_id, client_id) DO UPDATE SET
                   rating=excluded.rating, comment=excluded.comment,
                   created_at=CURRENT_TIMESTAMP""",
                (workout_id, client_id, rating, comment or None),
            )
            connection.execute("UPDATE workouts SET status='completed' WHERE id=?", (workout_id,))
            workout = connection.execute(
                """SELECT trainer_id, name FROM workouts
                   WHERE id=? AND client_id=?""",
                (workout_id, client_id),
            ).fetchone()
            message = (
                "OCENA TRENINGA\n"
                f"Trening: {workout['name']}\n"
                f"Ocena: {rating}/5\n"
                f"Komentar: {comment or 'Bez komentara.'}"
            )
            connection.execute(
                """INSERT INTO messages(
                       sender_id, receiver_id, text, message_type, rating_key
                   ) VALUES (?, ?, ?, 'workout_rating', ?)
                   ON CONFLICT(rating_key) DO UPDATE SET
                   text=excluded.text, created_at=CURRENT_TIMESTAMP""",
                (
                    client_id,
                    workout["trainer_id"],
                    message,
                    f"workout_rating:{workout_id}:{client_id}",
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def rate_trainer(self, trainer_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            eligible = connection.execute(
                """SELECT 1 FROM trainer_client_relations
                   WHERE trainer_id=? AND client_id=?
                     AND status='accepted' AND is_paid=1""",
                (trainer_id, client_id),
            ).fetchone()
            if eligible is None:
                raise ValueError("Mozete oceniti samo trenera sa aktivnom clanarinom.")
            connection.execute(
                """INSERT INTO trainer_ratings(client_id, trainer_id, rating, comment)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(client_id, trainer_id) DO UPDATE SET
                   rating=excluded.rating, comment=excluded.comment,
                   created_at=CURRENT_TIMESTAMP""",
                (client_id, trainer_id, rating, comment or None),
            )
            connection.commit()
        finally:
            connection.close()

    def rate_exercise(self, workout_id, exercise_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """INSERT INTO exercise_ratings(workout_id, exercise_id, client_id, rating, comment)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(workout_id, exercise_id, client_id) DO UPDATE SET
                   rating=excluded.rating, comment=excluded.comment,
                   created_at=CURRENT_TIMESTAMP""",
                (workout_id, exercise_id, client_id, rating, comment or None),
            )
            rated_exercise = connection.execute(
                """SELECT w.trainer_id, w.name AS workout_name,
                          e.name AS exercise_name
                   FROM workouts w
                   JOIN workout_exercises we ON we.workout_id=w.id
                   JOIN exercises e ON e.id=we.exercise_id
                   WHERE w.id=? AND we.exercise_id=? AND w.client_id=?""",
                (workout_id, exercise_id, client_id),
            ).fetchone()
            message = (
                "OCENA VEZBE\n"
                f"Trening: {rated_exercise['workout_name']}\n"
                f"Vezba: {rated_exercise['exercise_name']}\n"
                f"Ocena: {rating}/5\n"
                f"Komentar: {comment or 'Bez komentara.'}"
            )
            connection.execute(
                """INSERT INTO messages(
                       sender_id, receiver_id, text, message_type, rating_key
                   ) VALUES (?, ?, ?, 'exercise_rating', ?)
                   ON CONFLICT(rating_key) DO UPDATE SET
                   text=excluded.text, created_at=CURRENT_TIMESTAMP""",
                (
                    client_id,
                    rated_exercise["trainer_id"],
                    message,
                    f"exercise_rating:{workout_id}:{exercise_id}:{client_id}",
                ),
            )
            connection.commit()
        finally:
            connection.close()

    # --------------------- INTERNE OCENE KLIJENATA ----------------------
    def save_client_rating(self, trainer_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            connection.execute(
                """INSERT INTO client_ratings(trainer_id, client_id, rating, comment)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                   rating=excluded.rating, comment=excluded.comment,
                   created_at=CURRENT_TIMESTAMP""",
                (trainer_id, client_id, rating, comment or None),
            )
            connection.commit()
        finally:
            connection.close()

    def list_client_ratings(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT cr.rating, cr.comment, cr.created_at,
                       t.first_name || ' ' || t.last_name AS trainer_name
                FROM client_ratings cr
                JOIN users t ON t.id=cr.trainer_id
                WHERE cr.client_id=?
                ORDER BY cr.created_at DESC
                """,
                (client_id,),
            ).fetchall()
        finally:
            connection.close()

    # ----------------------- PLACANJA I PORUKE -------------------------
    def sync_membership_statuses(self):
        connection = self.connection_factory()
        try:
            connection.execute(
                """UPDATE trainer_client_relations
                   SET is_paid=CASE
                       WHEN status='accepted' AND EXISTS (
                           SELECT 1 FROM payments p
                           WHERE p.trainer_id=trainer_client_relations.trainer_id
                             AND p.client_id=trainer_client_relations.client_id
                             AND p.status='paid'
                             AND p.paid_at <= CURRENT_TIMESTAMP
                             AND p.valid_until > CURRENT_TIMESTAMP
                       ) THEN 1
                       ELSE 0
                   END"""
            )
            connection.commit()
        finally:
            connection.close()

    def pay_monthly_subscription(self, trainer_id, client_id):
        connection = self.connection_factory()
        try:
            relation = connection.execute(
                """SELECT monthly_price FROM trainer_client_relations
                   WHERE trainer_id=? AND client_id=? AND status='accepted'""",
                (trainer_id, client_id),
            ).fetchone()
            if relation is None:
                raise ValueError("Nemate prihvacen odnos sa trenerom.")
            active_payment = connection.execute(
                """SELECT valid_until FROM payments
                   WHERE trainer_id=? AND client_id=? AND status='paid'
                     AND valid_until > CURRENT_TIMESTAMP
                   ORDER BY valid_until DESC LIMIT 1""",
                (trainer_id, client_id),
            ).fetchone()
            if active_payment:
                raise ValueError(
                    f"Clanarina vec vazi do {active_payment['valid_until']}."
                )
            connection.execute(
                """INSERT INTO payments(
                       trainer_id, client_id, amount, status, paid_at, valid_until
                   ) VALUES (?, ?, ?, 'paid', CURRENT_TIMESTAMP,
                             datetime(CURRENT_TIMESTAMP, '+1 month'))""",
                (trainer_id, client_id, relation["monthly_price"]),
            )
            connection.execute(
                """UPDATE trainer_client_relations
                   SET is_paid=1,
                       expiration_date = (
                       SELECT valid_until
                       FROM payments
                       WHERE trainer_id=? AND client_id=? AND status='paid'
                       ORDER BY id DESC
                       LIMIT 1
                   )
                   WHERE trainer_id=? AND client_id=?""",
                (trainer_id, client_id, trainer_id, client_id),
            )
            connection.commit()
        finally:
            connection.close()

    def create_membership_notifications(self, client_id):
        connection = self.connection_factory()
        try:
            payments = connection.execute(
                """SELECT p.id, p.trainer_id, p.valid_until,
                          t.first_name || ' ' || t.last_name AS trainer_name
                   FROM payments p
                   JOIN users t ON t.id=p.trainer_id
                   WHERE p.client_id=? AND p.status='paid'""",
                (client_id,),
            ).fetchall()
            for payment in payments:
                state = connection.execute(
                    """SELECT
                           datetime(?) <= CURRENT_TIMESTAMP AS expired,
                           date(?) <= date('now', 'localtime', '+3 days') AS soon""",
                    (payment["valid_until"], payment["valid_until"]),
                ).fetchone()
                if state["expired"]:
                    notification_type = "expired"
                    message = (
                        f"Clanarina kod trenera {payment['trainer_name']} je istekla "
                        f"{payment['valid_until']}."
                    )
                elif state["soon"]:
                    notification_type = "expiring"
                    message = (
                        f"Clanarina kod trenera {payment['trainer_name']} istice "
                        f"{payment['valid_until']}."
                    )
                else:
                    continue
                connection.execute(
                    """INSERT OR IGNORE INTO notifications(
                           client_id, trainer_id, payment_id,
                           notification_type, message
                       ) VALUES (?, ?, ?, ?, ?)""",
                    (
                        client_id,
                        payment["trainer_id"],
                        payment["id"],
                        notification_type,
                        message,
                    ),
                )
            connection.commit()
        finally:
            connection.close()

    def list_unread_notifications(self, client_id):
        connection = self.connection_factory()
        try:
            rows = connection.execute(
                """SELECT id, client_id, trainer_id, payment_id,
                          notification_type, message, is_read, created_at
                   FROM notifications
                   WHERE client_id=? AND is_read=0
                   ORDER BY created_at, id""",
                (client_id,),
            ).fetchall()
            return [self._to_notification(row) for row in rows]
        finally:
            connection.close()

    def mark_notification_read(self, notification_id, client_id):
        connection = self.connection_factory()
        try:
            connection.execute(
                """UPDATE notifications SET is_read=1
                   WHERE id=? AND client_id=?""",
                (notification_id, client_id),
            )
            connection.commit()
        finally:
            connection.close()

    def send_message(self, sender_id, receiver_id, text):
        connection = self.connection_factory()
        try:
            connection.execute(
                "INSERT INTO messages(sender_id, receiver_id, text) VALUES (?, ?, ?)",
                (sender_id, receiver_id, text),
            )
            connection.commit()
        finally:
            connection.close()

    def get_admin_id(self):
        connection = self.connection_factory()
        try:
            row = connection.execute(
                """
                SELECT id
                FROM users
                WHERE role = 'admin' AND registration_status = 'approved'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
            return row["id"] if row else None
        finally:
            connection.close()

    def list_messages(self, first_user_id, second_user_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT m.*, u.username AS sender_username
                FROM messages m JOIN users u ON u.id=m.sender_id
                WHERE (m.sender_id=? AND m.receiver_id=?)
                   OR (m.sender_id=? AND m.receiver_id=?)
                ORDER BY m.created_at, m.id
                """, (first_user_id, second_user_id, second_user_id, first_user_id)
            ).fetchall()
        finally:
            connection.close()
