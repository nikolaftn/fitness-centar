import customtkinter as ctk


COMMON_FIELDS = (
    ("username", "Username", False),
    ("password", "Password", True),
    ("password_confirmation", "Confirm password", True),
    ("first_name", "First name", False),
    ("last_name", "Last name", False),
    ("birth_date", "Date of birth (YYYY-MM-DD)", False),
)


class BaseRegistrationView:
    """Shared layout for registration windows."""

    title = "Registration"
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
    title = "Client Registration"

class TrainerRegistrationView(BaseRegistrationView):
    title = "Trainer Registration Request"
    additional_fields = (
        ("education", "Education", False),
        ("years_of_experience", "Years of experience", False),
        ("price_per_training", "Price per session", False),
    )
