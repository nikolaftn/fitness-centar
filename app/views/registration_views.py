import customtkinter as ctk


COMMON_FIELDS = (
    ("username", "Korisnicko ime", False),
    ("password", "Lozinka", True),
    ("password_confirmation", "Potvrda lozinke", True),
    ("first_name", "Ime", False),
    ("last_name", "Prezime", False),
    ("birth_date", "Datum rodjenja (GGGG-MM-DD)", False),
)


class BaseRegistrationView:
    """Zajednicki izgled prozora za registraciju."""

    title = "Registracija"
    additional_fields = ()

    def __init__(self, parent, controller):
        self.controller = controller
        self.entries = {}
        self.window = ctk.CTkToplevel(parent)
        self.window.title(self.title)
        self.window.geometry("470x610")
        self.window.minsize(430, 500)
        self.window.transient(parent)
        self.window.grab_set()

        form = ctk.CTkScrollableFrame(self.window)
        form.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            form,
            text=self.title,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(0, 18))
        for field_name, label, secret in COMMON_FIELDS + self.additional_fields:
            ctk.CTkLabel(form, text=label).pack(anchor="w")
            entry = ctk.CTkEntry(form, show="*" if secret else "")
            entry.pack(fill="x", pady=(3, 11))
            self.entries[field_name] = entry

        ctk.CTkButton(form, text="Potvrdi", command=self._submit).pack(fill="x", pady=(10, 0))
        self.message_label = ctk.CTkLabel(form, text="", justify="left", wraplength=380)
        self.message_label.pack(fill="x", pady=(12, 0))
        self.entries["username"].focus_set()

    def _submit(self):
        self.controller.submit({name: entry.get() for name, entry in self.entries.items()})

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")

    def close(self):
        self.window.destroy()


class ClientRegistrationView(BaseRegistrationView):
    title = "Registracija klijenta"

class TrainerRegistrationView(BaseRegistrationView):
    title = "Zahtev za registraciju trenera"
    additional_fields = (
        ("education", "Obrazovanje", False),
        ("years_of_experience", "Godine iskustva", False),
        ("price_per_training", "Cena pojedinacnog treninga", False),
    )
