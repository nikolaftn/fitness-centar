class AdminService:
    def __init__(self, trainer_repository):
        self.trainer_repository = trainer_repository

    def get_dashboard_data(self):
        return (
            self.trainer_repository.list_pending_registrations(),
            self.trainer_repository.list_trainers_by_average_rating(),
        )

    def decide_trainer_registration(self, trainer_id, decision):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Neispravna odluka.")
        return self.trainer_repository.decide_registration(trainer_id, decision)

