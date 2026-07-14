import customtkinter as ctk


class LoginView:
    """Prozor za unos podataka za prijavu."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Prijava")
        self.window.geometry("430x310")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        frame = ctk.CTkFrame(self.window)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text="Prijava",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(24, 18))

        ctk.CTkLabel(frame, text="Korisnicko ime").pack(anchor="w", padx=28)
        self.username_entry = ctk.CTkEntry(frame)
        self.username_entry.pack(fill="x", padx=28, pady=(4, 14))

        ctk.CTkLabel(frame, text="Lozinka").pack(anchor="w", padx=28)
        self.password_entry = ctk.CTkEntry(frame, show="*")
        self.password_entry.pack(fill="x", padx=28, pady=(4, 18))

        ctk.CTkButton(frame, text="Prijavi se", command=self._submit).pack(fill="x", padx=28)
        self.message_label = ctk.CTkLabel(frame, text="", wraplength=350, justify="left")
        self.message_label.pack(fill="x", padx=28, pady=(12, 0))
        self.window.bind("<Return>", lambda _event: self._submit())
        self.username_entry.focus_set()

    def _submit(self):
        self.controller.submit(self.username_entry.get(), self.password_entry.get())

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")

    def close(self):
        self.window.destroy()
