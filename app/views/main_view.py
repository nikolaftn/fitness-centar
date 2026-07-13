import tkinter as tk
from tkinter import messagebox


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
            command=lambda: self.controller.show_not_implemented_message("Prijava"),
        ).pack(pady=6)

        tk.Button(
            buttons_frame,
            text="Registracija klijenta",
            width=30,
            command=lambda: self.controller.show_not_implemented_message(
                "Registracija klijenta"
            ),
        ).pack(pady=6)

        tk.Button(
            buttons_frame,
            text="Zahtev za registraciju trenera",
            width=30,
            command=lambda: self.controller.show_not_implemented_message(
                "Zahtev za registraciju trenera"
            ),
        ).pack(pady=6)

        self.user_count_label.pack(pady=(30, 0))

    def refresh_user_count(self):
        total = self.controller.get_user_count()
        self.user_count_label.config(text=f"Broj korisnika u bazi: {total}")

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def run(self):
        self.root.mainloop()
