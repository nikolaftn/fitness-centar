import customtkinter as ctk


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainView:
    """Pocetni CustomTkinter prozor aplikacije."""

    def __init__(self, controller):
        self.controller = controller
        self.root = ctk.CTk()
        self.root.title("Fitness centar")
        self.root.geometry("800x500")
        self.root.minsize(650, 420)

        self.user_count_label = ctk.CTkLabel(self.root, text="")
        self._build_layout()
        self.refresh_user_count()

    def _build_layout(self):
        title = ctk.CTkLabel(
            self.root,
            text="Fitness centar",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=(55, 12))

        subtitle = ctk.CTkLabel(
            self.root,
            text="Pocetni ekran aplikacije",
            font=ctk.CTkFont(size=14),
        )
        subtitle.pack(pady=(0, 25))

        buttons_frame = ctk.CTkFrame(self.root)
        buttons_frame.pack()

        ctk.CTkButton(
            buttons_frame,
            text="Prijava",
            width=300,
            command=self.controller.open_login,
        ).pack(fill="x", padx=22, pady=8)

        ctk.CTkButton(
            buttons_frame,
            text="Registracija klijenta",
            width=300,
            command=self.controller.open_client_registration,
        ).pack(fill="x", padx=22, pady=8)

        ctk.CTkButton(
            buttons_frame,
            text="Zahtev za registraciju trenera",
            width=300,
            command=self.controller.open_trainer_registration,
        ).pack(fill="x", padx=22, pady=8)

        self.admin_setup_button = ctk.CTkButton(
            buttons_frame,
            text="Pocetno podesavanje administratora",
            width=300,
            command=self.controller.open_initial_admin_setup,
        )
        if not self.controller.has_admin():
            self.admin_setup_button.pack(fill="x", padx=22, pady=8)

        self.user_count_label.pack(pady=(30, 0))

    def refresh_user_count(self):
        total = self.controller.get_user_count()
        self.user_count_label.configure(text=f"Broj korisnika u bazi: {total}")

    def refresh_after_admin_created(self):
        self.admin_setup_button.pack_forget()
        self.refresh_user_count()

    def run(self):
        self.root.mainloop()
