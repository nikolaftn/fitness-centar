import customtkinter as ctk


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainView:
    """Main CustomTkinter application window."""

    def __init__(self, controller):
        self.controller = controller
        self.root = ctk.CTk()
        self.root.title("Fitness centar")
        self.root.geometry("800x500")
        self.root.minsize(650, 420)

        self._build_layout()

    def _build_layout(self):
        title = ctk.CTkLabel(
            self.root,
            text="Fitness centar",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=(55, 12))

        buttons_frame = ctk.CTkFrame(self.root)
        buttons_frame.pack()

        ctk.CTkButton(
            buttons_frame,
            text="Login",
            width=300,
            command=self.controller.open_login,
        ).pack(fill="x", padx=22, pady=8)

        ctk.CTkButton(
            buttons_frame,
            text="Client Registration",
            width=300,
            command=self.controller.open_client_registration,
        ).pack(fill="x", padx=22, pady=8)

        ctk.CTkButton(
            buttons_frame,
            text="Trainer Registration Request",
            width=300,
            command=self.controller.open_trainer_registration,
        ).pack(fill="x", padx=22, pady=8)

    def run(self):
        self.root.mainloop()
