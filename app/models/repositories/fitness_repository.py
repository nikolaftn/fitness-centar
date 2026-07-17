import calendar
from datetime import date, datetime, timedelta

from app.database import get_connection
from app.models.domain.fitness_entities import (
    ClientRating,
    Equipment,
    Exercise,
    ExerciseRating,
    Message,
    Notification,
    Payment,
    TrainerCenterPayment,
    TrainerClientRelation,
    TrainerRating,
    Workout,
    WorkoutExercise,
    WorkoutRating,
)


class FitnessRepository:
    """Cita objekte iz memorije, a svaku izmenu odmah cuva u SQLite bazi."""

    CENTER_RENT_AMOUNT = 30000.0

    def __init__(self, application_data, connection_factory=get_connection):
        self.data = application_data
        self.connection_factory = connection_factory

    # ------------------------- TRENERI I ODNOSI -------------------------
    def list_available_trainers(self, client_id):
        profiles = []
        for profile in self.data.trainer_profiles.values():
            trainer = profile.user
            if trainer.registration_status != "approved":
                continue

            relation = self.data.trainer_client_relations.get(
                (trainer.id, client_id)
            )
            if relation and relation.status in {"pending", "accepted"}:
                continue

            self._set_trainer_rating_summary(profile)
            profiles.append(profile)

        return sorted(profiles, key=self._trainer_sort_key)

    def get_trainer_profile(self, trainer_id):
        return self.data.trainer_profiles.get(trainer_id)

    def update_trainer_profile(self, trainer_id, values):
        profile = self.data.trainer_profiles.get(trainer_id)
        if profile is None:
            raise ValueError("Profil trenera nije pronadjen.")

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?, birth_date = ?
                WHERE id = ?
                """,
                (
                    values["first_name"],
                    values["last_name"],
                    values["birth_date"],
                    trainer_id,
                ),
            )
            connection.execute(
                """
                UPDATE trainer_profiles
                SET education = ?, diploma_license = ?, biography = ?,
                    years_of_experience = ?, price_per_training = ?
                WHERE user_id = ?
                """,
                (
                    values["education"] or None,
                    values["diploma_license"] or None,
                    values["biography"] or None,
                    values["years_of_experience"],
                    values["price_per_training"],
                    trainer_id,
                ),
            )
            connection.execute(
                """
                UPDATE trainer_client_relations
                SET monthly_price = workouts_per_week * ? * 4
                WHERE trainer_id = ? AND status = 'accepted'
                """,
                (values["price_per_training"], trainer_id),
            )
            connection.commit()
        finally:
            connection.close()

        profile.user.first_name = values["first_name"]
        profile.user.last_name = values["last_name"]
        profile.user.birth_date = values["birth_date"]
        profile.education = values["education"] or None
        profile.diploma_license = values["diploma_license"] or None
        profile.biography = values["biography"] or None
        profile.years_of_experience = values["years_of_experience"]
        profile.price_per_training = values["price_per_training"]

        for relation in self.data.trainer_client_relations.values():
            if relation.trainer is profile.user and relation.status == "accepted":
                relation.monthly_price = (
                    relation.workouts_per_week * profile.price_per_training * 4
                )

    def get_trainer_price(self, trainer_id):
        profile = self.data.trainer_profiles.get(trainer_id)
        if profile is None:
            return None
        return profile.price_per_training

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
        monthly_price,
    ):
        trainer = self.data.users.get(trainer_id)
        client = self.data.users.get(client_id)
        if trainer is None or client is None:
            raise ValueError("Trener ili klijent nije pronadjen.")

        key = (trainer_id, client_id)
        relation = self.data.trainer_client_relations.get(key)
        if relation and relation.status == "pending":
            raise ValueError("Zahtev ovom treneru je vec poslat.")
        if relation and relation.status == "accepted":
            raise ValueError("Vec imate prihvacen odnos sa ovim trenerom.")

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO trainer_client_relations (
                    trainer_id, client_id, monthly_price, status,
                    workouts_per_week, goals, height_cm, weight_kg,
                    training_location, health_conditions
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                    monthly_price = excluded.monthly_price,
                    expiration_date = NULL, is_paid = 0, status = 'pending',
                    workouts_per_week = excluded.workouts_per_week,
                    goals = excluded.goals, height_cm = excluded.height_cm,
                    weight_kg = excluded.weight_kg,
                    training_location = excluded.training_location,
                    health_conditions = excluded.health_conditions
                """,
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

        if relation is None:
            relation = TrainerClientRelation(
                trainer,
                client,
                monthly_price,
                None,
                False,
                "pending",
                workouts_per_week,
                goals or None,
                height_cm,
                weight_kg,
                training_location,
                health_conditions or None,
            )
            self.data.trainer_client_relations[key] = relation
        else:
            relation.monthly_price = monthly_price
            relation.expiration_date = None
            relation.is_paid = False
            relation.status = "pending"
            relation.workouts_per_week = workouts_per_week
            relation.goals = goals or None
            relation.height_cm = height_cm
            relation.weight_kg = weight_kg
            relation.training_location = training_location
            relation.health_conditions = health_conditions or None

    def list_client_relations(self, client_id):
        relations = []
        for relation in self.data.trainer_client_relations.values():
            if relation.client.id != client_id:
                continue
            if relation.status in {"pending", "accepted"}:
                relations.append(relation)
        return sorted(
            relations,
            key=self._client_relation_sort_key,
        )

    def list_trainer_requests(self, trainer_id):
        requests = []
        for relation in self.data.trainer_client_relations.values():
            if relation.trainer.id == trainer_id and relation.status == "pending":
                requests.append(relation)
        return sorted(requests, key=self._relation_client_name)

    def decide_client_request(self, trainer_id, client_id, status):
        if status not in {"accepted", "rejected"}:
            raise ValueError("Neispravan status.")

        relation = self.data.trainer_client_relations.get((trainer_id, client_id))
        if relation is None or relation.status != "pending":
            return False

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                UPDATE trainer_client_relations
                SET status = ?, is_paid = 0, expiration_date = NULL
                WHERE trainer_id = ? AND client_id = ?
                """,
                (status, trainer_id, client_id),
            )
            connection.commit()
        finally:
            connection.close()

        relation.status = status
        relation.is_paid = False
        relation.expiration_date = None
        return True

    def list_accepted_clients(self, trainer_id):
        relations = []
        for relation in self.data.trainer_client_relations.values():
            if relation.trainer.id != trainer_id:
                continue
            if relation.status != "accepted" or not relation.is_paid:
                continue

            payment = self._active_payment(relation)
            if payment is None:
                continue
            relation.active_until = payment.valid_until
            relation.missed_count = self._count_missed(relation, payment)
            relations.append(relation)

        return sorted(relations, key=self._relation_client_name)

    # ------------------------------ VEZBE ------------------------------
    def list_exercises(self, trainer_id):
        exercises = []
        for exercise in self.data.exercises.values():
            if exercise.trainer.id == trainer_id:
                exercises.append(exercise)
        return sorted(exercises, key=self._object_name)

    def save_exercise(
        self,
        trainer_id,
        exercise_id,
        name,
        description,
        duration_minutes,
        equipment_id,
    ):
        trainer = self.data.users.get(trainer_id)
        if trainer is None or trainer.role != "trainer":
            raise ValueError("Trener nije pronadjen.")

        equipment = self.data.equipment.get(equipment_id)
        exercise = None
        if exercise_id is not None:
            exercise = self.data.exercises.get((trainer_id, exercise_id))
            if exercise is None:
                raise ValueError("Vezba ovog trenera nije pronadjena.")
        else:
            exercise_id = self._next_exercise_id(trainer_id)

        connection = self.connection_factory()
        try:
            if exercise is not None:
                connection.execute(
                    """
                    UPDATE exercises
                    SET name = ?, description = ?, duration_minutes = ?, equipment_id = ?
                    WHERE trainer_id = ? AND id = ?
                    """,
                    (
                        name,
                        description or None,
                        duration_minutes,
                        equipment_id,
                        trainer_id,
                        exercise_id,
                    ),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO exercises (
                        trainer_id, id, name, description,
                        duration_minutes, equipment_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trainer_id,
                        exercise_id,
                        name,
                        description or None,
                        duration_minutes,
                        equipment_id,
                    ),
                )
            connection.commit()
        finally:
            connection.close()

        if exercise is not None:
            exercise.name = name
            exercise.description = description or None
            exercise.duration_minutes = duration_minutes
            exercise.equipment = equipment
        else:
            exercise = Exercise(
                trainer,
                exercise_id,
                name,
                description or None,
                duration_minutes,
                equipment,
            )
            self.data.exercises[(trainer.id, exercise.id)] = exercise
        return exercise

    def create_exercise(self, trainer_id, name, description):
        return self.save_exercise(
            trainer_id, None, name, description, None, None
        )

    def delete_exercise(self, trainer_id, exercise_id):
        exercise = self.data.exercises.get((trainer_id, exercise_id))
        if exercise is None:
            raise ValueError("Vezba ovog trenera nije pronadjena.")

        connection = self.connection_factory()
        try:
            connection.execute(
                "DELETE FROM exercises WHERE trainer_id = ? AND id = ?",
                (trainer_id, exercise_id),
            )
            connection.commit()
        finally:
            connection.close()

        keys = list(self.data.workout_exercises.keys())
        for key in keys:
            item = self.data.workout_exercises[key]
            if item.exercise is exercise:
                del self.data.workout_exercises[key]

        rating_keys = list(self.data.exercise_ratings.keys())
        for key in rating_keys:
            rating = self.data.exercise_ratings[key]
            if rating.exercise is exercise:
                del self.data.exercise_ratings[key]

        self.data.exercises.pop((trainer_id, exercise_id), None)

    # ------------------------------ OPREMA ------------------------------
    def list_equipment(self):
        return sorted(self.data.equipment.values(), key=self._object_name)

    def save_equipment(self, equipment_id, name, category, description):
        connection = self.connection_factory()
        try:
            if equipment_id:
                connection.execute(
                    """
                    UPDATE equipment
                    SET name = ?, category = ?, description = ?
                    WHERE id = ?
                    """,
                    (name, category, description or None, equipment_id),
                )
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO equipment (name, category, description)
                    VALUES (?, ?, ?)
                    """,
                    (name, category, description or None),
                )
            connection.commit()
        finally:
            connection.close()

        if equipment_id:
            equipment = self.data.equipment[equipment_id]
            equipment.name = name
            equipment.category = category
            equipment.description = description or None
        else:
            equipment = Equipment(
                cursor.lastrowid, name, category, description or None
            )
            self.data.equipment[equipment.id] = equipment
        return equipment

    def delete_equipment(self, equipment_id):
        connection = self.connection_factory()
        try:
            connection.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
            connection.commit()
        finally:
            connection.close()

        equipment = self.data.equipment.pop(equipment_id, None)
        for exercise in self.data.exercises.values():
            if exercise.equipment is equipment:
                exercise.equipment = None

    # ------------------------------ TRENINZI ----------------------------
    def mark_overdue_workouts(self):
        today = date.today()
        changed_workouts = []
        for workout in self.data.workouts.values():
            if workout.status != "assigned":
                continue
            if date.fromisoformat(workout.scheduled_date) < today:
                changed_workouts.append(workout)

        if not changed_workouts:
            return

        connection = self.connection_factory()
        try:
            for workout in changed_workouts:
                connection.execute(
                    "UPDATE workouts SET status = 'missed' WHERE id = ?",
                    (workout.id,),
                )
            connection.commit()
        finally:
            connection.close()

        for workout in changed_workouts:
            workout.status = "missed"

    def get_active_membership_expiration(self, trainer_id, client_id):
        relation = self.data.trainer_client_relations.get((trainer_id, client_id))
        payment = self._active_payment(relation)
        if payment is None:
            return None
        return payment.valid_until

    def count_missed_workouts_in_active_membership(self, trainer_id, client_id):
        relation = self.data.trainer_client_relations.get((trainer_id, client_id))
        payment = self._active_payment(relation)
        if payment is None:
            return 0
        return self._count_missed(relation, payment)

    def create_workout(
        self,
        trainer_id,
        client_id,
        workout_name,
        exercise_assignments,
        scheduled_date,
    ):
        relation = self.data.trainer_client_relations.get((trainer_id, client_id))
        if relation is None:
            raise ValueError("Odnos trenera i klijenta nije pronadjen.")

        selected_assignments = []
        for assignment in exercise_assignments:
            exercise_id = assignment["exercise_id"]
            exercise = self.data.exercises.get((trainer_id, exercise_id))
            if exercise is None:
                raise ValueError("Izabrana vezba ne pripada ovom treneru.")
            selected_assignments.append((exercise, assignment))

        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO workouts (
                    trainer_id, client_id, name, scheduled_date, status
                ) VALUES (?, ?, ?, ?, 'assigned')
                """,
                (trainer_id, client_id, workout_name, scheduled_date),
            )
            workout_id = cursor.lastrowid
            order = 1
            for exercise, assignment in selected_assignments:
                connection.execute(
                    """
                    INSERT INTO workout_exercises (
                        workout_id, trainer_id, exercise_id, exercise_order,
                        sets, repetitions, duration_minutes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workout_id,
                        trainer_id,
                        exercise.id,
                        order,
                        assignment["sets"],
                        assignment["repetitions"],
                        assignment["duration_minutes"],
                    ),
                )
                order += 1
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        workout = Workout(
            workout_id, relation, workout_name, scheduled_date, "assigned"
        )
        self.data.workouts[workout.id] = workout
        order = 1
        for exercise, assignment in selected_assignments:
            item = WorkoutExercise(
                workout,
                exercise,
                order,
                assignment["sets"],
                assignment["repetitions"],
                assignment["duration_minutes"],
                False,
                None,
            )
            self.data.workout_exercises[(workout.id, exercise.id)] = item
            order += 1
        return workout

    def list_client_workouts(self, client_id, trainer_id):
        workouts = []
        for workout in self.data.workouts.values():
            if workout.client.id != client_id or workout.trainer.id != trainer_id:
                continue

            workout_rating = self.data.workout_ratings.get((workout.id, client_id))
            trainer_rating = self.data.trainer_ratings.get((client_id, trainer_id))
            workout.workout_rating = None
            workout.trainer_rating = None
            if workout_rating:
                workout.workout_rating = workout_rating.rating
            if trainer_rating:
                workout.trainer_rating = trainer_rating.rating
            workouts.append(workout)
        return sorted(workouts, key=self._object_id, reverse=True)

    def list_workout_exercises(self, workout_id, client_id):
        items = []
        for item in self.data.workout_exercises.values():
            if item.workout.id != workout_id:
                continue
            rating = self.data.exercise_ratings.get(
                (workout_id, item.exercise.id, client_id)
            )
            item.rating = None
            item.comment = None
            if rating:
                item.rating = rating.rating
                item.comment = rating.comment
            items.append(item)
        return sorted(items, key=self._exercise_order)

    def get_client_workout(self, workout_id, client_id):
        workout = self.data.workouts.get(workout_id)
        if workout is None or workout.client.id != client_id:
            return None
        return workout

    def set_workout_exercise_completed(
        self, workout_id, exercise_id, client_id, completed
    ):
        item = self.data.workout_exercises.get((workout_id, exercise_id))
        if item is None or item.workout.client.id != client_id:
            raise ValueError("Vezba nije pronadjena u ovom treningu.")

        completed_at = None
        if completed:
            completed_at = self._current_time()

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                UPDATE workout_exercises
                SET completed = ?, completed_at = ?
                WHERE workout_id = ? AND exercise_id = ?
                """,
                (int(completed), completed_at, workout_id, exercise_id),
            )
            connection.commit()
        finally:
            connection.close()

        item.completed = bool(completed)
        item.completed_at = completed_at

    def is_workout_exercise_completed(self, workout_id, exercise_id):
        item = self.data.workout_exercises.get((workout_id, exercise_id))
        return bool(item and item.completed)

    def all_workout_exercises_completed(self, workout_id):
        items = []
        for item in self.data.workout_exercises.values():
            if item.workout.id == workout_id:
                items.append(item)
        return bool(items) and all(item.completed for item in items)

    def rate_workout(self, workout_id, client_id, rating_value, comment):
        workout = self.get_client_workout(workout_id, client_id)
        if workout is None:
            raise ValueError("Trening nije pronadjen.")

        created_at = self._current_time()
        key = (workout_id, client_id)
        message_text = (
            "OCENA TRENINGA\n"
            f"Trening: {workout.name}\n"
            f"Ocena: {rating_value}/5\n"
            f"Komentar: {comment or 'Bez komentara.'}"
        )
        rating_key = f"workout_rating:{workout_id}:{client_id}"
        existing_message = self._find_message_by_rating_key(rating_key)

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO workout_ratings (
                    workout_id, client_id, rating, comment, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(workout_id, client_id) DO UPDATE SET
                    rating = excluded.rating, comment = excluded.comment,
                    created_at = excluded.created_at
                """,
                (workout_id, client_id, rating_value, comment or None, created_at),
            )
            connection.execute(
                "UPDATE workouts SET status = 'completed' WHERE id = ?",
                (workout_id,),
            )
            message_id = self._upsert_rating_message_in_database(
                connection,
                workout.client.id,
                workout.trainer.id,
                message_text,
                "workout_rating",
                rating_key,
                created_at,
                existing_message,
            )
            connection.commit()
        finally:
            connection.close()

        existing = self.data.workout_ratings.get(key)
        if existing:
            existing.rating = rating_value
            existing.comment = comment or None
            existing.created_at = created_at
        else:
            self.data.workout_ratings[key] = WorkoutRating(
                workout,
                workout.client,
                rating_value,
                comment or None,
                created_at,
            )
        workout.status = "completed"
        workout.workout_rating = rating_value
        self._save_rating_message_in_memory(
            message_id,
            workout.client,
            workout.trainer,
            message_text,
            "workout_rating",
            rating_key,
            created_at,
        )

    def rate_trainer(self, trainer_id, client_id, rating_value, comment):
        relation = self.data.trainer_client_relations.get((trainer_id, client_id))
        if relation is None or relation.status != "accepted" or not relation.is_paid:
            raise ValueError("Mozete oceniti samo trenera sa aktivnom clanarinom.")

        created_at = self._current_time()
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO trainer_ratings (
                    client_id, trainer_id, rating, comment, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(client_id, trainer_id) DO UPDATE SET
                    rating = excluded.rating, comment = excluded.comment,
                    created_at = excluded.created_at
                """,
                (client_id, trainer_id, rating_value, comment or None, created_at),
            )
            connection.commit()
        finally:
            connection.close()

        key = (client_id, trainer_id)
        existing = self.data.trainer_ratings.get(key)
        if existing:
            existing.rating = rating_value
            existing.comment = comment or None
            existing.created_at = created_at
        else:
            self.data.trainer_ratings[key] = TrainerRating(
                relation.client,
                relation.trainer,
                rating_value,
                comment or None,
                created_at,
            )

    def rate_exercise(
        self, workout_id, exercise_id, client_id, rating_value, comment
    ):
        item = self.data.workout_exercises.get((workout_id, exercise_id))
        if item is None or item.workout.client.id != client_id:
            raise ValueError("Vezba nije pronadjena u ovom treningu.")

        created_at = self._current_time()
        key = (workout_id, exercise_id, client_id)
        message_text = (
            "OCENA VEZBE\n"
            f"Trening: {item.workout.name}\n"
            f"Vezba: {item.exercise.name}\n"
            f"Ocena: {rating_value}/5\n"
            f"Komentar: {comment or 'Bez komentara.'}"
        )
        rating_key = f"exercise_rating:{workout_id}:{exercise_id}:{client_id}"
        existing_message = self._find_message_by_rating_key(rating_key)

        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO exercise_ratings (
                    workout_id, exercise_id, client_id,
                    rating, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(workout_id, exercise_id, client_id) DO UPDATE SET
                    rating = excluded.rating, comment = excluded.comment,
                    created_at = excluded.created_at
                """,
                (
                    workout_id,
                    exercise_id,
                    client_id,
                    rating_value,
                    comment or None,
                    created_at,
                ),
            )
            message_id = self._upsert_rating_message_in_database(
                connection,
                item.workout.client.id,
                item.workout.trainer.id,
                message_text,
                "exercise_rating",
                rating_key,
                created_at,
                existing_message,
            )
            connection.commit()
        finally:
            connection.close()

        existing = self.data.exercise_ratings.get(key)
        if existing:
            existing.rating = rating_value
            existing.comment = comment or None
            existing.created_at = created_at
        else:
            self.data.exercise_ratings[key] = ExerciseRating(
                item,
                item.workout.client,
                rating_value,
                comment or None,
                created_at,
            )
        item.rating = rating_value
        item.comment = comment or None
        self._save_rating_message_in_memory(
            message_id,
            item.workout.client,
            item.workout.trainer,
            message_text,
            "exercise_rating",
            rating_key,
            created_at,
        )

    # --------------------- INTERNE OCENE KLIJENATA ----------------------
    def save_client_rating(self, trainer_id, client_id, rating_value, comment):
        trainer = self.data.users.get(trainer_id)
        client = self.data.users.get(client_id)
        if trainer is None or client is None:
            raise ValueError("Trener ili klijent nije pronadjen.")

        created_at = self._current_time()
        connection = self.connection_factory()
        try:
            connection.execute(
                """
                INSERT INTO client_ratings (
                    trainer_id, client_id, rating, comment, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(trainer_id, client_id) DO UPDATE SET
                    rating = excluded.rating, comment = excluded.comment,
                    created_at = excluded.created_at
                """,
                (trainer_id, client_id, rating_value, comment or None, created_at),
            )
            connection.commit()
        finally:
            connection.close()

        key = (trainer_id, client_id)
        existing = self.data.client_ratings.get(key)
        if existing:
            existing.rating = rating_value
            existing.comment = comment or None
            existing.created_at = created_at
        else:
            self.data.client_ratings[key] = ClientRating(
                trainer, client, rating_value, comment or None, created_at
            )

    def list_client_ratings(self, client_id):
        ratings = []
        for rating in self.data.client_ratings.values():
            if rating.client.id == client_id:
                ratings.append(rating)
        return sorted(ratings, key=self._created_at, reverse=True)

    # ----------------------- PLACANJA I PORUKE -------------------------
    def sync_membership_statuses(self):
        changed_relations = []
        for relation in self.data.trainer_client_relations.values():
            is_paid = relation.status == "accepted" and bool(
                self._active_payment(relation, check_relation=False)
            )
            if relation.is_paid != is_paid:
                relation.is_paid = is_paid
                changed_relations.append(relation)

        if not changed_relations:
            return

        connection = self.connection_factory()
        try:
            for relation in changed_relations:
                connection.execute(
                    """
                    UPDATE trainer_client_relations
                    SET is_paid = ?
                    WHERE trainer_id = ? AND client_id = ?
                    """,
                    (int(relation.is_paid), relation.trainer.id, relation.client.id),
                )
            connection.commit()
        finally:
            connection.close()

    def pay_monthly_subscription(self, trainer_id, client_id):
        relation = self.data.trainer_client_relations.get((trainer_id, client_id))
        if relation is None or relation.status != "accepted":
            raise ValueError("Nemate prihvacen odnos sa trenerom.")

        active_payment = self._active_payment(relation, check_relation=False)
        if active_payment:
            raise ValueError(
                f"Clanarina vec vazi do {active_payment.valid_until}."
            )

        paid_at = datetime.now()
        valid_until = self._add_one_month(paid_at)
        paid_text = self._format_time(paid_at)
        valid_text = self._format_time(valid_until)

        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO payments (
                    trainer_id, client_id, amount, status, paid_at, valid_until
                ) VALUES (?, ?, ?, 'paid', ?, ?)
                """,
                (
                    trainer_id,
                    client_id,
                    relation.monthly_price,
                    paid_text,
                    valid_text,
                ),
            )
            connection.execute(
                """
                UPDATE trainer_client_relations
                SET is_paid = 1, expiration_date = ?
                WHERE trainer_id = ? AND client_id = ?
                """,
                (valid_text, trainer_id, client_id),
            )
            connection.commit()
        finally:
            connection.close()

        payment = Payment(
            cursor.lastrowid,
            relation,
            relation.monthly_price,
            "paid",
            paid_text,
            valid_text,
        )
        self.data.payments[payment.id] = payment
        relation.is_paid = True
        relation.expiration_date = valid_text

    def get_center_rent_status(self, trainer_id):
        payments = []
        for payment in self.data.trainer_center_payments.values():
            if payment.trainer.id == trainer_id and payment.status == "paid":
                payments.append(payment)
        if not payments:
            return None
        return max(payments, key=self._valid_until)

    def pay_center_rent(self, trainer_id):
        active_payment = self.get_center_rent_status(trainer_id)
        if active_payment and self._is_time_range_active(
            active_payment.paid_at, active_payment.valid_until
        ):
            raise ValueError(
                f"Zakup centra vec vazi do {active_payment.valid_until}."
            )

        trainer = self.data.users.get(trainer_id)
        if trainer is None:
            raise ValueError("Trener nije pronadjen.")

        paid_at = datetime.now()
        valid_until = self._add_one_month(paid_at)
        paid_text = self._format_time(paid_at)
        valid_text = self._format_time(valid_until)

        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO trainer_center_payments (
                    trainer_id, amount, status, paid_at, valid_until
                ) VALUES (?, ?, 'paid', ?, ?)
                """,
                (trainer_id, self.CENTER_RENT_AMOUNT, paid_text, valid_text),
            )
            connection.commit()
        finally:
            connection.close()

        payment = TrainerCenterPayment(
            cursor.lastrowid,
            trainer,
            self.CENTER_RENT_AMOUNT,
            "paid",
            paid_text,
            valid_text,
        )
        self.data.trainer_center_payments[payment.id] = payment

    def list_center_rent_statuses(self):
        rows = []
        for profile in self.data.trainer_profiles.values():
            if profile.user.registration_status != "approved":
                continue
            rows.append((profile, self.get_center_rent_status(profile.user.id)))
        return sorted(rows, key=self._center_rent_row_name)

    def create_membership_notifications(self, client_id):
        client = self.data.users.get(client_id)
        now = datetime.now()
        for payment in list(self.data.payments.values()):
            if payment.client is not client or payment.status != "paid":
                continue

            valid_until = self._parse_time(payment.valid_until)
            notification_type = None
            if valid_until <= now:
                notification_type = "expired"
                message_text = (
                    f"Clanarina kod trenera {payment.trainer.full_name} je istekla "
                    f"{payment.valid_until}."
                )
            elif valid_until.date() <= (now + timedelta(days=3)).date():
                notification_type = "expiring"
                message_text = (
                    f"Clanarina kod trenera {payment.trainer.full_name} istice "
                    f"{payment.valid_until}."
                )

            if notification_type is None:
                continue
            if self._notification_exists(payment, notification_type):
                continue
            self._create_notification(payment, notification_type, message_text)

    def list_unread_notifications(self, client_id):
        notifications = []
        for notification in self.data.notifications.values():
            if notification.client.id == client_id and not notification.is_read:
                notifications.append(notification)
        return sorted(
            notifications,
            key=self._notification_sort_key,
        )

    def mark_notification_read(self, notification_id, client_id):
        notification = self.data.notifications.get(notification_id)
        if notification is None or notification.client.id != client_id:
            return

        connection = self.connection_factory()
        try:
            connection.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ?",
                (notification.id,),
            )
            connection.commit()
        finally:
            connection.close()
        notification.is_read = True

    def send_message(self, sender_id, receiver_id, text):
        sender = self.data.users.get(sender_id)
        receiver = self.data.users.get(receiver_id)
        if sender is None or receiver is None:
            raise ValueError("Posiljalac ili primalac nije pronadjen.")

        created_at = self._current_time()
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO messages (
                    sender_id, receiver_id, text, message_type,
                    rating_key, created_at
                ) VALUES (?, ?, ?, 'text', NULL, ?)
                """,
                (sender_id, receiver_id, text, created_at),
            )
            connection.commit()
        finally:
            connection.close()

        message = Message(
            cursor.lastrowid,
            sender,
            receiver,
            text,
            "text",
            None,
            created_at,
        )
        self.data.messages[message.id] = message

    def get_admin_id(self):
        admins = []
        for user in self.data.users.values():
            if user.role == "admin" and user.registration_status == "approved":
                admins.append(user)
        if not admins:
            return None
        return min(admins, key=self._object_id).id

    def list_messages(self, first_user_id, second_user_id):
        messages = []
        for message in self.data.messages.values():
            first_direction = (
                message.sender.id == first_user_id
                and message.receiver.id == second_user_id
            )
            second_direction = (
                message.sender.id == second_user_id
                and message.receiver.id == first_user_id
            )
            if first_direction or second_direction:
                messages.append(message)
        return sorted(messages, key=self._message_sort_key)

    # ---------------------------- POMOCNO -------------------------------
    def _set_trainer_rating_summary(self, profile):
        ratings = []
        for rating in self.data.trainer_ratings.values():
            if rating.trainer is profile.user:
                ratings.append(rating.rating)
        profile.rating_count = len(ratings)
        profile.average_rating = None
        if ratings:
            profile.average_rating = round(sum(ratings) / len(ratings), 2)

    def _next_exercise_id(self, trainer_id):
        largest_id = 0
        for exercise in self.data.exercises.values():
            if exercise.trainer.id != trainer_id:
                continue
            if exercise.id > largest_id:
                largest_id = exercise.id
        return largest_id + 1

    @staticmethod
    def _trainer_sort_key(profile):
        has_no_rating = profile.average_rating is None
        average = profile.average_rating or 0
        return (
            has_no_rating,
            -average,
            profile.last_name.lower(),
            profile.first_name.lower(),
        )

    def _active_payment(self, relation, check_relation=True):
        if relation is None:
            return None
        if check_relation and (relation.status != "accepted" or not relation.is_paid):
            return None

        active_payments = []
        for payment in self.data.payments.values():
            if payment.relation is not relation or payment.status != "paid":
                continue
            if self._is_time_range_active(payment.paid_at, payment.valid_until):
                active_payments.append(payment)
        if not active_payments:
            return None
        return max(active_payments, key=self._valid_until)

    def _count_missed(self, relation, payment):
        total = 0
        start_date = self._parse_time(payment.paid_at).date()
        end_date = self._parse_time(payment.valid_until).date()
        for workout in self.data.workouts.values():
            if workout.relation is not relation or workout.status != "missed":
                continue
            workout_date = date.fromisoformat(workout.scheduled_date)
            if start_date <= workout_date < end_date:
                total += 1
        return total

    @staticmethod
    def _client_relation_sort_key(relation):
        return (
            relation.status != "accepted",
            relation.trainer.last_name.lower(),
            relation.trainer.first_name.lower(),
        )

    @staticmethod
    def _relation_client_name(relation):
        return relation.client.full_name.lower()

    @staticmethod
    def _object_name(item):
        return item.name.lower()

    @staticmethod
    def _object_id(item):
        return item.id

    @staticmethod
    def _exercise_order(item):
        return item.exercise_order

    @staticmethod
    def _created_at(item):
        return item.created_at

    @staticmethod
    def _valid_until(payment):
        return payment.valid_until

    @staticmethod
    def _center_rent_row_name(row):
        profile = row[0]
        return profile.full_name.lower()

    @staticmethod
    def _notification_sort_key(notification):
        return notification.created_at, notification.id

    @staticmethod
    def _message_sort_key(message):
        return message.created_at, message.id

    def _notification_exists(self, payment, notification_type):
        for notification in self.data.notifications.values():
            if (
                notification.payment is payment
                and notification.notification_type == notification_type
            ):
                return True
        return False

    def _create_notification(self, payment, notification_type, message_text):
        created_at = self._current_time()
        connection = self.connection_factory()
        try:
            cursor = connection.execute(
                """
                INSERT INTO notifications (
                    client_id, trainer_id, payment_id, notification_type,
                    message, is_read, created_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    payment.client.id,
                    payment.trainer.id,
                    payment.id,
                    notification_type,
                    message_text,
                    created_at,
                ),
            )
            connection.commit()
        finally:
            connection.close()

        notification = Notification(
            cursor.lastrowid,
            payment.client,
            payment.trainer,
            payment,
            notification_type,
            message_text,
            False,
            created_at,
        )
        self.data.notifications[notification.id] = notification

    @staticmethod
    def _upsert_rating_message_in_database(
        connection,
        sender_id,
        receiver_id,
        text,
        message_type,
        rating_key,
        created_at,
        existing_message,
    ):
        if existing_message:
            connection.execute(
                """
                UPDATE messages SET text = ?, created_at = ? WHERE id = ?
                """,
                (text, created_at, existing_message.id),
            )
            return existing_message.id

        cursor = connection.execute(
            """
            INSERT INTO messages (
                sender_id, receiver_id, text, message_type,
                rating_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sender_id, receiver_id, text, message_type, rating_key, created_at),
        )
        return cursor.lastrowid

    def _find_message_by_rating_key(self, rating_key):
        for message in self.data.messages.values():
            if message.rating_key == rating_key:
                return message
        return None

    def _save_rating_message_in_memory(
        self,
        message_id,
        sender,
        receiver,
        text,
        message_type,
        rating_key,
        created_at,
    ):
        for message in self.data.messages.values():
            if message.rating_key == rating_key:
                message.text = text
                message.created_at = created_at
                return
        message = Message(
            message_id,
            sender,
            receiver,
            text,
            message_type,
            rating_key,
            created_at,
        )
        self.data.messages[message.id] = message

    @staticmethod
    def _parse_time(value):
        return datetime.fromisoformat(value)

    @classmethod
    def _is_time_range_active(cls, paid_at, valid_until):
        now = datetime.now()
        return cls._parse_time(paid_at) <= now < cls._parse_time(valid_until)

    @staticmethod
    def _add_one_month(value):
        year = value.year
        month = value.month + 1
        if month == 13:
            month = 1
            year += 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(value.day, last_day)
        return value.replace(year=year, month=month, day=day)

    @staticmethod
    def _format_time(value):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def _current_time(cls):
        return cls._format_time(datetime.now())
