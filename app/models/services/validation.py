from datetime import date


def validate_common_registration(data):
    labels = {
        "username": "Username",
        "password": "Password",
        "password_confirmation": "Confirm password",
        "first_name": "First name",
        "last_name": "Last name",
        "birth_date": "Date of birth",
    }
    for field, label in labels.items():
        if not data.get(field, "").strip():
            return f"The '{label}' field is required."

    username = data["username"].strip()
    if len(username) < 3 or any(character.isspace() for character in username):
        return "Username must contain at least 3 characters and no spaces."
    if len(data["password"]) < 6:
        return "Password must contain at least 6 characters."
    if data["password"] != data["password_confirmation"]:
        return "Password and confirmation do not match."
    return validate_profile_data(data)


def validate_profile_data(data):
    if not data["first_name"].strip() or not data["last_name"].strip():
        return "First and last name are required."
    try:
        birth_date = date.fromisoformat(data["birth_date"].strip())
    except ValueError:
        return "Date of birth must use the YYYY-MM-DD format."
    if birth_date > date.today():
        return "Date of birth cannot be in the future."
    return None


def parse_rating(value):
    try:
        rating = int(value)
    except ValueError as error:
        raise ValueError("Rating must be a whole number from 1 to 5.") from error
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be from 1 to 5.")
    return rating


def parse_client_request(data):
    try:
        workouts = int(data["workouts_per_week"])
        height = float(data["height_cm"].replace(",", "."))
        weight = float(data["weight_kg"].replace(",", "."))
    except ValueError as error:
        raise ValueError("Workouts per week, height, and weight must be numbers.") from error
    if not 1 <= workouts <= 7:
        raise ValueError("Workouts per week must be from 1 to 7.")
    if data["training_location"] not in {"gym", "home", "both"}:
        raise ValueError("Location must be gym, home, or both.")
    return {
        "workouts_per_week": workouts,
        "goals": data["goals"],
        "height_cm": height,
        "weight_kg": weight,
        "training_location": data["training_location"],
        "health_conditions": data["health_conditions"],
    }

