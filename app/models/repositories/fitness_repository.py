from app.database import get_connection


class FitnessRepository:
    """SQL operacije za kompletan tok klijenta i trenera."""

    def __init__(self, connection_factory=get_connection):
        self.connection_factory = connection_factory

    # ------------------------- TRENERI I ODNOSI -------------------------
    def list_available_trainers(self):
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
                WHERE u.role = 'trainer' AND u.registration_status = 'approved'
                GROUP BY u.id
                ORDER BY average_rating IS NULL, average_rating DESC,
                         u.last_name, u.first_name
                """
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

    def create_client_request(self, trainer_id, client_id, workouts_per_week,
                              goals, height_cm, weight_kg, training_location,
                              health_conditions):
        connection = self.connection_factory()
        try:
            profile = connection.execute(
                "SELECT price_per_training FROM trainer_profiles WHERE user_id=?",
                (trainer_id,),
            ).fetchone()
            if profile is None:
                raise ValueError("Izabrani trener nema profil.")
            monthly_price = profile["price_per_training"] * workouts_per_week * 4
            connection.execute(
                """
                INSERT INTO trainer_client_relations(
                    trainer_id, client_id, monthly_price, status,
                    workouts_per_week, goals, height_cm, weight_kg,
                    training_location, health_conditions
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                    monthly_price=excluded.monthly_price,
                    expiration_date=NULL, status='pending',
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
            return connection.execute(
                """
                SELECT r.*, u.first_name || ' ' || u.last_name AS trainer_name,
                       u.username AS trainer_username
                FROM trainer_client_relations r
                JOIN users u ON u.id=r.trainer_id
                WHERE r.client_id=?
                ORDER BY r.status='accepted' DESC, u.last_name, u.first_name
                """, (client_id,)
            ).fetchall()
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
                WHERE r.trainer_id=?
                ORDER BY r.status='pending' DESC, u.last_name, u.first_name
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
                """UPDATE trainer_client_relations SET status=?
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
            return connection.execute(
                """
                SELECT u.id, u.username,
                       u.first_name || ' ' || u.last_name AS client_name,
                       r.workouts_per_week, r.monthly_price, r.goals,
                       r.height_cm, r.weight_kg, r.training_location,
                       r.health_conditions,
                       (SELECT COUNT(*) FROM workouts w
                        WHERE w.trainer_id=r.trainer_id
                          AND w.client_id=r.client_id
                          AND w.status='missed') AS missed_count
                FROM trainer_client_relations r
                JOIN users u ON u.id=r.client_id
                WHERE r.trainer_id=? AND r.status='accepted'
                ORDER BY u.last_name, u.first_name
                """, (trainer_id,)
            ).fetchall()
        finally:
            connection.close()

    # ------------------------------ VEZBE ------------------------------
    def list_exercises(self):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """SELECT e.id, e.name, e.description, e.video_url,
                          e.duration_minutes, e.equipment_id,
                          q.name AS equipment_name
                   FROM exercises e
                   LEFT JOIN equipment q ON q.id = e.equipment_id
                   ORDER BY e.name"""
            ).fetchall()
        finally:
            connection.close()

    def save_exercise(self, exercise_id, name, description, video_url,
                      duration_minutes, equipment_id):
        connection = self.connection_factory()
        try:
            if exercise_id:
                connection.execute(
                    """UPDATE exercises SET name=?, description=?, video_url=?,
                       duration_minutes=?, equipment_id=? WHERE id=?""",
                    (name, description or None, video_url or None,
                     duration_minutes, equipment_id, exercise_id),
                )
            else:
                connection.execute(
                    """INSERT INTO exercises(
                           name, description, video_url, duration_minutes, equipment_id
                       ) VALUES (?, ?, ?, ?, ?)""",
                    (name, description or None, video_url or None,
                     duration_minutes, equipment_id),
                )
            connection.commit()
        finally:
            connection.close()

    def create_exercise(self, name, description, video_url):
        self.save_exercise(None, name, description, video_url, None, None)

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
            return connection.execute(
                "SELECT id, name, category, description FROM equipment ORDER BY name"
            ).fetchall()
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
    def _ensure_assignment_allowed(self, connection, trainer_id, client_id):
        missed = connection.execute(
            """
            SELECT COUNT(*) AS total FROM workouts w
            WHERE w.trainer_id=? AND w.client_id=? AND w.status='missed'
            """, (trainer_id, client_id)
        ).fetchone()["total"]
        if missed >= 2:
            raise ValueError(
                "Klijent ima najmanje dva neodradjena treninga. "
                "Dodeljivanje novih treninga je automatski blokirano."
            )

    def create_workout(self, trainer_id, client_id, workout_name, exercise_ids,
                       scheduled_date=None):
        connection = self.connection_factory()
        try:
            self._ensure_assignment_allowed(connection, trainer_id, client_id)
            relation = connection.execute(
                """SELECT 1 FROM trainer_client_relations
                   WHERE trainer_id=? AND client_id=? AND status='accepted'""",
                (trainer_id, client_id),
            ).fetchone()
            if relation is None:
                raise ValueError("Klijent nije prihvacen kod ovog trenera.")
            cursor = connection.execute(
                """INSERT INTO workouts(trainer_id, client_id, name, scheduled_date)
                   VALUES (?, ?, ?, ?)""",
                (trainer_id, client_id, workout_name, scheduled_date or None),
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

    def list_trainer_workouts(self, trainer_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT w.id, w.name, w.scheduled_date, w.status,
                       w.client_id, u.first_name || ' ' || u.last_name AS client_name
                FROM workouts w
                JOIN users u ON u.id=w.client_id
                WHERE w.trainer_id=? ORDER BY w.id DESC
                """, (trainer_id,)
            ).fetchall()
        finally:
            connection.close()

    def update_workout_status(self, trainer_id, workout_id, status):
        if status not in {"assigned", "completed", "missed"}:
            raise ValueError("Neispravan status treninga.")
        connection = self.connection_factory()
        try:
            connection.execute(
                "UPDATE workouts SET status=? WHERE id=? AND trainer_id=?",
                (status, workout_id, trainer_id),
            )
            connection.commit()
        finally:
            connection.close()

    def copy_workout_to_client(self, trainer_id, source_workout_id, target_client_id):
        connection = self.connection_factory()
        try:
            self._ensure_assignment_allowed(connection, trainer_id, target_client_id)
            workout = connection.execute(
                "SELECT * FROM workouts WHERE id=? AND trainer_id=?",
                (source_workout_id, trainer_id),
            ).fetchone()
            if workout is None:
                raise ValueError("Trening nije pronadjen.")
            relation = connection.execute(
                """SELECT 1 FROM trainer_client_relations
                   WHERE trainer_id=? AND client_id=? AND status='accepted'""",
                (trainer_id, target_client_id),
            ).fetchone()
            if relation is None:
                raise ValueError("Ciljni klijent nije prihvacen.")
            cursor = connection.execute(
                """INSERT INTO workouts(trainer_id, client_id, name, scheduled_date, status)
                   VALUES (?, ?, ?, ?, 'assigned')""",
                (trainer_id, target_client_id, workout["name"] + " - kopija",
                 workout["scheduled_date"]),
            )
            new_workout_id = cursor.lastrowid
            exercises = connection.execute(
                "SELECT * FROM workout_exercises WHERE workout_id=? ORDER BY exercise_order",
                (source_workout_id,),
            ).fetchall()
            connection.executemany(
                """INSERT INTO workout_exercises(workout_id, exercise_id,
                   exercise_order, sets, repetitions, duration_minutes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [(new_workout_id, exercise["exercise_id"], exercise["exercise_order"],
                  exercise["sets"], exercise["repetitions"], exercise["duration_minutes"])
                 for exercise in exercises],
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list_client_workouts(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT w.id, w.name, w.scheduled_date, w.status,
                       t.id AS trainer_id,
                       t.first_name || ' ' || t.last_name AS trainer_name,
                       wr.rating AS workout_rating, tr.rating AS trainer_rating
                FROM workouts w
                JOIN users t ON t.id=w.trainer_id
                LEFT JOIN workout_ratings wr ON wr.workout_id=w.id AND wr.client_id=w.client_id
                LEFT JOIN trainer_ratings tr ON tr.trainer_id=w.trainer_id AND tr.client_id=w.client_id
                WHERE w.client_id=? ORDER BY w.id DESC
                """, (client_id,)
            ).fetchall()
        finally:
            connection.close()

    def list_workout_exercises(self, workout_id, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT e.id, e.name, e.description, e.video_url,
                       q.name AS equipment_name,
                       COALESCE(we.duration_minutes, e.duration_minutes) AS duration_minutes,
                       we.exercise_order, er.rating, er.comment
                FROM workout_exercises we JOIN exercises e ON e.id=we.exercise_id
                LEFT JOIN equipment q ON q.id=e.equipment_id
                LEFT JOIN exercise_ratings er ON er.workout_id=we.workout_id
                  AND er.exercise_id=we.exercise_id AND er.client_id=?
                WHERE we.workout_id=? ORDER BY we.exercise_order
                """, (client_id, workout_id)
            ).fetchall()
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
            connection.commit()
        finally:
            connection.close()

    def rate_trainer(self, trainer_id, client_id, rating, comment):
        connection = self.connection_factory()
        try:
            eligible = connection.execute(
                """SELECT 1 FROM trainer_client_relations
                   WHERE trainer_id=? AND client_id=? AND status IN ('accepted','expired')""",
                (trainer_id, client_id),
            ).fetchone()
            if eligible is None:
                raise ValueError("Trenera moze oceniti samo njegov sadasnji ili bivsi klijent.")
            existing = connection.execute(
                "SELECT 1 FROM trainer_ratings WHERE trainer_id=? AND client_id=?",
                (trainer_id, client_id),
            ).fetchone()
            if existing:
                raise ValueError("Trenera mozete oceniti samo jednom.")
            connection.execute(
                "INSERT INTO trainer_ratings(client_id, trainer_id, rating, comment) VALUES (?, ?, ?, ?)",
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

    def list_client_ratings_for_trainers(self):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """
                SELECT cr.*, c.first_name || ' ' || c.last_name AS client_name,
                       t.first_name || ' ' || t.last_name AS trainer_name
                FROM client_ratings cr
                JOIN users c ON c.id=cr.client_id
                JOIN users t ON t.id=cr.trainer_id
                ORDER BY cr.created_at DESC
                """
            ).fetchall()
        finally:
            connection.close()

    # ----------------------- PLACANJA I PORUKE -------------------------
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
            connection.commit()
        finally:
            connection.close()

    def list_payments_for_client(self, client_id):
        connection = self.connection_factory()
        try:
            return connection.execute(
                """SELECT p.*, t.first_name || ' ' || t.last_name AS trainer_name
                   FROM payments p JOIN users t ON t.id=p.trainer_id
                   WHERE p.client_id=? ORDER BY p.paid_at DESC""", (client_id,)
            ).fetchall()
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
