class AdminService:
    def __init__(self, trainer_repository, fitness_repository):
        self.trainer_repository = trainer_repository
        self.fitness_repository = fitness_repository

    def get_dashboard_data(self):
        return (
            self.trainer_repository.list_pending_registrations(),
            self.trainer_repository.list_trainers_by_average_rating(),
            self.fitness_repository.list_center_rent_statuses(),
        )

    def decide_trainer_registration(self, trainer_id, decision):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Invalid decision.")
        return self.trainer_repository.decide_registration(trainer_id, decision)

    def delete_trainer(self, trainer_id):
        if not self.trainer_repository.delete_trainer(trainer_id):
            raise ValueError("The trainer does not exist or is no longer approved.")

    def get_messages(self, admin_id, trainer_id):
        self._validate_trainer(trainer_id)
        return self.fitness_repository.list_messages(admin_id, trainer_id)

    def send_message(self, admin_id, trainer_id, text):
        self._validate_trainer(trainer_id)
        text = text.strip()
        if not text:
            raise ValueError("A message cannot be empty.")
        self.fitness_repository.send_message(admin_id, trainer_id, text)

    def _validate_trainer(self, trainer_id):
        if not self.trainer_repository.is_approved_trainer(trainer_id):
            raise ValueError("The selected trainer does not exist or is no longer approved.")

