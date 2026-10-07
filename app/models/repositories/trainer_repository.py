from app.database import get_connection


class TrainerRepository:
    """Works with trainers already loaded in memory."""

    def __init__(self, application_data, connection_factory=get_connection):
        self.data = application_data
        self.connection_factory = connection_factory

    def list_pending_registrations(self):
        profiles = []
        for profile in self.data.trainer_profiles.values():
            if profile.user.registration_status == "pending":
                profiles.append(profile)
        return sorted(profiles, key=self._registration_sort_key)

    def decide_registration(self, trainer_id, decision):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Decision must be 'approved' or 'rejected'.")

        trainer = self.data.users.get(trainer_id)
        if trainer is None or trainer.role != "trainer":
            return False
        if trainer.registration_status != "pending":
            return False

        connection = self.connection_factory()
        try:
            connection.execute(
                "UPDATE users SET registration_status = ? WHERE id = ?",
                (decision, trainer.id),
            )
            connection.commit()
        finally:
            connection.close()

        trainer.registration_status = decision
        return True

    def list_trainers_by_average_rating(self):
        trainers = []
        for profile in self.data.trainer_profiles.values():
            if profile.user.registration_status != "approved":
                continue

            ratings = []
            for rating in self.data.trainer_ratings.values():
                if rating.trainer is profile.user:
                    ratings.append(rating.rating)

            rating_count = len(ratings)
            average_rating = None
            if rating_count > 0:
                average_rating = round(sum(ratings) / rating_count, 2)
            trainers.append((profile, average_rating, rating_count))

        return sorted(trainers, key=self._rating_sort_key)

    def is_approved_trainer(self, trainer_id):
        trainer = self.data.users.get(trainer_id)
        return bool(
            trainer
            and trainer.role == "trainer"
            and trainer.registration_status == "approved"
        )

    def delete_trainer(self, trainer_id):
        if not self.is_approved_trainer(trainer_id):
            return False

        connection = self.connection_factory()
        try:
            connection.execute("DELETE FROM users WHERE id = ?", (trainer_id,))
            connection.commit()
        finally:
            connection.close()

        # SQLite cascaded the delete to related rows. Reconnecting
        # the in-memory data here is simpler and safer than manually clearing 14 collections.
        self.data.load_all()
        return True

    @staticmethod
    def _registration_sort_key(profile):
        return profile.user.created_at, profile.user.id

    @staticmethod
    def _rating_sort_key(trainer_data):
        profile, average_rating, rating_count = trainer_data
        has_no_rating = average_rating is None
        average = average_rating or 0
        return (
            has_no_rating,
            -average,
            -rating_count,
            profile.last_name.lower(),
            profile.first_name.lower(),
        )
