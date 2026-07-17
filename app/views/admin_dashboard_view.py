import tkinter as tk
from tkinter import ttk


class AdminDashboardView:
    """Administratorski prozor za obradu zahteva trenera."""

    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Administrator")
        self.window.geometry("1100x820")
        self.window.minsize(900, 700)

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

        tk.Label(
            self.window,
            text="Mesecni zakup fitnes centra",
            font=("Arial", 12, "bold"),
            padx=24,
            anchor="w",
        ).pack(fill="x", pady=(14, 4))
        rents_frame = tk.Frame(self.window, padx=24)
        rents_frame.pack(fill="both", expand=True)
        rent_columns = (
            "name",
            "username",
            "amount",
            "paid_at",
            "valid_until",
            "status",
        )
        self.rents_table = ttk.Treeview(
            rents_frame,
            columns=rent_columns,
            show="headings",
            height=5,
        )
        rent_headings = {
            "name": "Trener",
            "username": "Korisnicko ime",
            "amount": "Iznos",
            "paid_at": "Datum uplate",
            "valid_until": "Vazi do",
            "status": "Status",
        }
        rent_widths = {
            "name": 170,
            "username": 130,
            "amount": 100,
            "paid_at": 160,
            "valid_until": 160,
            "status": 100,
        }
        for column in rent_columns:
            self.rents_table.heading(column, text=rent_headings[column])
            self.rents_table.column(column, width=rent_widths[column], anchor="w")
        self.rents_table.tag_configure("active", foreground="darkgreen")
        self.rents_table.tag_configure("expired", foreground="firebrick")
        self.rents_table.tag_configure("unpaid", foreground="darkorange")
        self.rents_table.pack(side="left", fill="both", expand=True)
        rents_scrollbar = ttk.Scrollbar(
            rents_frame, orient="vertical", command=self.rents_table.yview
        )
        rents_scrollbar.pack(side="right", fill="y")
        self.rents_table.configure(yscrollcommand=rents_scrollbar.set)

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

    def show_center_rents(self, payments):
        status_text = {
            "active": "Placeno",
            "expired": "Isteklo",
            "unpaid": "Nije placeno",
        }
        for item in self.rents_table.get_children():
            self.rents_table.delete(item)
        for payment in payments:
            status = payment["rent_status"]
            self.rents_table.insert(
                "",
                "end",
                iid=str(payment["id"]),
                values=(
                    f"{payment['first_name']} {payment['last_name']}",
                    payment["username"],
                    f"{payment['amount']:.2f}" if payment["amount"] else "-",
                    payment["paid_at"] or "-",
                    payment["valid_until"] or "-",
                    status_text[status],
                ),
                tags=(status,),
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

    def show_error(self, message):
        self.message_label.config(text=message, fg="firebrick")

    def show_info(self, message):
        self.message_label.config(text=message, fg="darkgreen")
