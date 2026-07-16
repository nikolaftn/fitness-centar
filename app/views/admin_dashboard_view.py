import tkinter as tk
from tkinter import messagebox, ttk


class AdminDashboardView:
    """Administratorski prozor za obradu zahteva trenera."""

    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Administrator")
        self.window.geometry("1000x700")
        self.window.minsize(850, 580)

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

        tk.Label(
            self.window,
            text="Treneri sortirani po prosecnoj oceni",
            font=("Arial", 12, "bold"),
            padx=24,
            anchor="w",
        ).pack(fill="x", pady=(14, 4))
        ratings_frame = tk.Frame(self.window, padx=24)
        ratings_frame.pack(fill="both", expand=True)
        rating_columns = ("name", "username", "education", "average", "count")
        self.ratings_table = ttk.Treeview(
            ratings_frame,
            columns=rating_columns,
            show="headings",
            selectmode="browse",
            height=5,
        )
        rating_headings = {
            "name": "Ime i prezime",
            "username": "Korisnicko ime",
            "education": "Obrazovanje",
            "average": "Prosecna ocena",
            "count": "Broj ocena",
        }
        for column in rating_columns:
            self.ratings_table.heading(column, text=rating_headings[column])
            self.ratings_table.column(column, width=150, anchor="w")
        self.ratings_table.pack(side="left", fill="both", expand=True)
        ratings_scrollbar = ttk.Scrollbar(
            ratings_frame, orient="vertical", command=self.ratings_table.yview
        )
        ratings_scrollbar.pack(side="right", fill="y")
        self.ratings_table.configure(yscrollcommand=ratings_scrollbar.set)

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
            buttons,
            text="Ukloni trenera",
            width=16,
            fg="firebrick",
            command=self.controller.delete_selected_trainer,
        ).pack(side="left", padx=8)
        tk.Button(
            buttons,
            text="Otvori chat",
            width=16,
            command=self.controller.open_trainer_chat,
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

    def show_sorted_trainers(self, trainers):
        for item in self.ratings_table.get_children():
            self.ratings_table.delete(item)
        for trainer in trainers:
            self.ratings_table.insert(
                "",
                "end",
                iid=str(trainer["id"]),
                values=(
                    f"{trainer['first_name']} {trainer['last_name']}",
                    trainer["username"],
                    trainer["education"] or "",
                    trainer["average_rating"] or "Nema",
                    trainer["rating_count"],
                ),
            )

    def get_selected_trainer_id(self):
        selection = self.table.selection()
        return int(selection[0]) if selection else None

    def get_selected_existing_trainer_id(self):
        selection = self.ratings_table.selection()
        return int(selection[0]) if selection else None

    def get_selected_existing_trainer_name(self):
        selection = self.ratings_table.selection()
        if not selection:
            return None
        return self.ratings_table.item(selection[0], "values")[0]

    def confirm_trainer_deletion(self, trainer_name):
        return messagebox.askyesno(
            "Uklanjanje trenera",
            f"Da li sigurno zelite da uklonite trenera {trainer_name}?",
            parent=self.window,
        )

    def show_error(self, message):
        self.message_label.config(text=message, fg="firebrick")

    def show_info(self, message):
        self.message_label.config(text=message, fg="darkgreen")
