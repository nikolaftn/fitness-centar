import tkinter as tk
from tkinter import messagebox


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
        self.window = tk.Toplevel(parent)
        self.window.title(self.title)
        self.window.geometry("470x610")
        self.window.minsize(430, 500)
        self.window.transient(parent)
        self.window.grab_set()

        canvas = tk.Canvas(self.window, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, padx=30, pady=24)
        form.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=form, anchor="nw", width=450)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(form, text=self.title, font=("Arial", 18, "bold")).pack(pady=(0, 18))
        for field_name, label, secret in COMMON_FIELDS + self.additional_fields:
            tk.Label(form, text=label).pack(anchor="w")
            entry = tk.Entry(form, show="*" if secret else "")
            entry.pack(fill="x", pady=(3, 11))
            self.entries[field_name] = entry

        tk.Button(form, text="Potvrdi", command=self._submit).pack(fill="x", pady=(10, 0))
        self.entries["username"].focus_set()

    def _submit(self):
        self.controller.submit({name: entry.get() for name, entry in self.entries.items()})

    def show_error(self, message):
        messagebox.showerror(self.title, message, parent=self.window)

    def show_info(self, message):
        messagebox.showinfo(self.title, message, parent=self.window)

    def close(self):
        self.window.destroy()


class ClientRegistrationView(BaseRegistrationView):
    title = "Registracija klijenta"


class InitialAdminView(BaseRegistrationView):
    title = "Pocetno podesavanje administratora"


class TrainerRegistrationView(BaseRegistrationView):
    title = "Zahtev za registraciju trenera"
    additional_fields = (
        ("education", "Obrazovanje", False),
        ("years_of_experience", "Godine iskustva", False),
        ("price_per_training", "Cena pojedinacnog treninga", False),
    )
