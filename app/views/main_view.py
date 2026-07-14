import tkinter as tk


class MainView:
    """Pocetni Tkinter prozor aplikacije."""

    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Fitness centar")
        self.root.geometry("800x500")
        self.root.minsize(650, 420)

        self.user_count_label = tk.Label(self.root)
        self._build_layout()
        self.refresh_user_count()

    def _build_layout(self):
        title = tk.Label(
            self.root,
            text="Fitness centar",
            font=("Arial", 24, "bold"),
        )
        title.pack(pady=(55, 12))

        subtitle = tk.Label(
            self.root,
            text="Pocetni ekran aplikacije",
            font=("Arial", 12),
        )
        subtitle.pack(pady=(0, 25))

        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack()

        tk.Button(
            buttons_frame,
            text="Prijava",
            width=30,
            command=self.controller.open_login,
        ).pack(pady=6)

        tk.Button(
            buttons_frame,
            text="Registracija klijenta",
            width=30,
            command=self.controller.open_client_registration,
        ).pack(pady=6)

        tk.Button(
            buttons_frame,
            text="Zahtev za registraciju trenera",
            width=30,
            command=self.controller.open_trainer_registration,
        ).pack(pady=6)

        self.admin_setup_button = tk.Button(
            buttons_frame,
            text="Pocetno podesavanje administratora",
            width=30,
            command=self.controller.open_initial_admin_setup,
        )
        if not self.controller.has_admin():
            self.admin_setup_button.pack(pady=6)

        self.user_count_label.pack(pady=(30, 0))

    def refresh_user_count(self):
        total = self.controller.get_user_count()
        self.user_count_label.config(text=f"Broj korisnika u bazi: {total}")

    def refresh_after_admin_created(self):
        self.admin_setup_button.pack_forget()
        self.refresh_user_count()

    def run(self):
        self.root.mainloop()
