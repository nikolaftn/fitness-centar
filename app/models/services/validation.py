from datetime import date


def validate_common_registration(data):
    labels = {
        "username": "Korisnicko ime",
        "password": "Lozinka",
        "password_confirmation": "Potvrda lozinke",
        "first_name": "Ime",
        "last_name": "Prezime",
        "birth_date": "Datum rodjenja",
    }
    for field, label in labels.items():
        if not data.get(field, "").strip():
            return f"Polje '{label}' je obavezno."

    username = data["username"].strip()
    if len(username) < 3 or any(character.isspace() for character in username):
        return "Korisnicko ime mora imati najmanje 3 znaka i ne sme sadrzati razmake."
    if len(data["password"]) < 6:
        return "Lozinka mora imati najmanje 6 znakova."
    if data["password"] != data["password_confirmation"]:
        return "Lozinka i potvrda lozinke se ne podudaraju."
    return validate_profile_data(data)


def validate_profile_data(data):
    if not data["first_name"].strip() or not data["last_name"].strip():
        return "Ime i prezime su obavezni."
    try:
        birth_date = date.fromisoformat(data["birth_date"].strip())
    except ValueError:
        return "Datum rodjenja mora biti u formatu GGGG-MM-DD."
    if birth_date > date.today():
        return "Datum rodjenja ne moze biti u buducnosti."
    return None


def parse_rating(value):
    try:
        rating = int(value)
    except ValueError as error:
        raise ValueError("Ocena mora biti ceo broj od 1 do 5.") from error
    if not 1 <= rating <= 5:
        raise ValueError("Ocena mora biti od 1 do 5.")
    return rating


def parse_client_request(data):
    try:
        workouts = int(data["workouts_per_week"])
        height = float(data["height_cm"].replace(",", "."))
        weight = float(data["weight_kg"].replace(",", "."))
    except ValueError as error:
        raise ValueError("Broj treninga, visina i tezina moraju biti brojevi.") from error
    if not 1 <= workouts <= 7:
        raise ValueError("Broj treninga mora biti od 1 do 7.")
    if data["training_location"] not in {"gym", "home", "both"}:
        raise ValueError("Lokacija mora biti gym, home ili both.")
    return {
        "workouts_per_week": workouts,
        "goals": data["goals"],
        "height_cm": height,
        "weight_kg": weight,
        "training_location": data["training_location"],
        "health_conditions": data["health_conditions"],
    }

