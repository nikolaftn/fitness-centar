from datetime import date


def validate_common_registration(data):
    required_labels = {
        "username": "Korisnicko ime",
        "password": "Lozinka",
        "password_confirmation": "Potvrda lozinke",
        "first_name": "Ime",
        "last_name": "Prezime",
        "birth_date": "Datum rodjenja",
    }
    for field, label in required_labels.items():
        if not data.get(field, "").strip():
            return f"Polje '{label}' je obavezno."

    username = data["username"].strip()
    if len(username) < 3 or any(character.isspace() for character in username):
        return (
            "Korisnicko ime mora imati najmanje 3 znaka "
            "i ne sme sadrzati razmake."
        )
    if len(data["password"]) < 6:
        return "Lozinka mora imati najmanje 6 znakova."
    if data["password"] != data["password_confirmation"]:
        return "Lozinka i potvrda lozinke se ne podudaraju."

    try:
        birth_date = date.fromisoformat(data["birth_date"].strip())
    except ValueError:
        return "Datum rodjenja mora biti u formatu GGGG-MM-DD."
    if birth_date > date.today():
        return "Datum rodjenja ne moze biti u buducnosti."
    return None
