from app.models.services.validation import validate_common_registration


class RegistrationService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register_client(self, data):
        self._validate(data)
        return self.user_repository.create_client(
            data["username"].strip(), data["password"], data["first_name"].strip(),
            data["last_name"].strip(), data["birth_date"].strip(),
        )

    def register_trainer(self, data):
        self._validate(data)
        try:
            years = int(data["years_of_experience"].strip())
            price = float(data["price_per_training"].strip().replace(",", "."))
        except ValueError as error:
            raise ValueError("Godine iskustva i cena moraju biti brojevi.") from error
        if years < 0 or price < 0:
            raise ValueError("Godine iskustva i cena ne mogu biti negativni.")
        return self.user_repository.create_trainer(
            data["username"].strip(), data["password"], data["first_name"].strip(),
            data["last_name"].strip(), data["birth_date"].strip(),
            data["education"].strip(), years, price,
        )

    @staticmethod
    def _validate(data):
        error = validate_common_registration(data)
        if error:
            raise ValueError(error)

