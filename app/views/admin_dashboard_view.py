import tkinter as tk
from tkinter import ttk


class AdminDashboardView:
    """Administratorski prozor za obradu zahteva trenera."""

    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Administrator")
        self.window.geometry("920x520")
        self.window.minsize(760, 420)

        header = tk.Frame(self.window, padx=24, pady=18)
        header.pack(fill="x")
        tk.Label(
            header,
            text=f"Administrator: {user.full_name}",
            font=("Arial", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(header, text="Zahtevi za registraciju trenera").pack(anchor="w")

        table_frame = tk.Frame(self.window, padx=24)
        table_frame.pack(fill="both", expand=True)
        columns = ("username", "name", "education", "experience", "price")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "username": "Korisnicko ime",
            "name": "Ime i prezime",
            "education": "Obrazovanje",
            "experience": "Iskustvo",
            "price": "Cena treninga",
        }
        widths = {
            "username": 130,
            "name": 170,
            "education": 230,
            "experience": 90,
            "price": 110,
        }
        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=widths[column], anchor="w")
        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scrollbar.set)

        self.message_label = tk.Label(self.window, padx=24, anchor="w")
        self.message_label.pack(fill="x", pady=(10, 0))

        buttons = tk.Frame(self.window, padx=24, pady=18)
        buttons.pack(fill="x")
        tk.Button(
            buttons, text="Odobri", width=16, command=self.controller.approve_selected
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            buttons, text="Odbij", width=16, command=self.controller.reject_selected
        ).pack(side="left", padx=8)
        tk.Button(
            buttons, text="Osvezi", width=16, command=self.controller.refresh
        ).pack(side="right")

    def show_registrations(self, registrations):
        for item in self.table.get_children():
            self.table.delete(item)
        for registration in registrations:
            self.table.insert(
                "",
                "end",
                iid=str(registration.user_id),
                values=(
                    registration.username,
                    registration.full_name,
                    registration.education,
                    registration.years_of_experience,
                    f"{registration.price_per_training:.2f}",
                ),
            )

    def get_selected_trainer_id(self):
        selection = self.table.selection()
        return int(selection[0]) if selection else None

    def show_error(self, message):
        self.message_label.config(text=message, fg="firebrick")

    def show_info(self, message):
        self.message_label.config(text=message, fg="darkgreen")
