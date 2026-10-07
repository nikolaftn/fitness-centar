import customtkinter as ctk

from app.views.list_panel import ListPanel


class TrainerDashboardView:
    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Trainer")
        self.window.geometry("1280x760")
        self.window.minsize(1100, 680)
        self.window.grab_set()

        self._build_header(user)
        self._build_center_rent_panel()
        self._build_content()

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=24, pady=(0, 14))

    def _build_header(self, user):
        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 8))

        ctk.CTkLabel(
            header,
            text=f"Trainer: {user.full_name}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Refresh",
            width=90,
            command=self.controller.refresh,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header,
            text="Chat with Administrator",
            command=self.controller.open_admin_chat,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header,
            text="Equipment",
            width=100,
            command=self.controller.open_equipment_management,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header,
            text="Exercises",
            width=100,
            command=self.controller.open_exercise_management,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header,
            text="My Profile",
            width=110,
            command=self.controller.open_profile,
        ).pack(side="right", padx=(8, 0))

    def _build_center_rent_panel(self):
        panel = ctk.CTkFrame(self.window)
        panel.pack(fill="x", padx=24, pady=(0, 4))

        self.center_rent_label = ctk.CTkLabel(
            panel,
            text="Checking fitness center rent...",
            anchor="w",
        )
        self.center_rent_label.pack(
            side="left", fill="x", expand=True, padx=14, pady=10
        )

        self.center_rent_button = ctk.CTkButton(
            panel,
            text="Pay monthly rent",
            command=self.controller.pay_center_rent,
        )
        self.center_rent_button.pack(side="right", padx=14, pady=10)

    def _build_content(self):
        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._build_requests_panel(content)
        self._build_clients_panel(content)

    def _build_requests_panel(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            panel,
            text="New Client Requests",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.requests_list = ListPanel(panel, height=250)
        self.requests_list.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        ctk.CTkLabel(
            panel,
            text="Selected Request Details",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(2, 4))
        self.request_details = ctk.CTkLabel(
            panel,
            text="Select a request.",
            justify="left",
            anchor="nw",
            wraplength=520,
        )
        self.request_details.pack(fill="x", padx=14, pady=(0, 10))

        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.pack(fill="x", padx=10, pady=(0, 14))
        ctk.CTkButton(
            buttons,
            text="View Client Ratings",
            command=self.controller.open_request_client_ratings,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            buttons,
            text="Accept Request",
            command=self.controller.accept_selected_request,
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            buttons,
            text="Reject Request",
            fg_color="#6b7280",
            command=self.controller.reject_selected_request,
        ).pack(side="right", padx=4)

    def _build_clients_panel(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            panel,
            text="Clients with Active Memberships",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.clients_list = ListPanel(panel, height=350)
        self.clients_list.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.client_details = ctk.CTkLabel(
            panel,
            text="Select a client.",
            justify="left",
            anchor="nw",
            wraplength=520,
        )
        self.client_details.pack(fill="x", padx=14, pady=(0, 10))

        first_row = ctk.CTkFrame(panel, fg_color="transparent")
        first_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkButton(
            first_row,
            text="Assign Workout",
            command=self.controller.open_workout_assignment,
        ).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(
            first_row,
            text="Open Chat",
            command=self.controller.open_client_chat,
        ).pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(
            panel,
            text="Rate Selected Client",
            command=self.controller.open_client_rating,
        ).pack(fill="x", padx=14, pady=(0, 14))

    @staticmethod
    def _format_request(relation):
        return f"{relation.client.full_name} ({relation.client.username})"

    def _format_client(self, relation):
        client_data = self.client_membership_data[relation.client.id]
        return (
            f"{relation.client.full_name} ({relation.client.username})\n"
            f"Membership until: {client_data['active_until']} | "
            f"Propusteno: {client_data['missed_count']}"
        )

    def show_requests(self, rows):
        self.request_details.configure(text="Select a request.")
        self.requests_list.set_rows(
            rows,
            "client_id",
            self._format_request,
            self._show_request_details,
        )

    def _show_request_details(self, relation):
        self.request_details.configure(
            text=(
                f"Client: {relation.client.full_name}\n"
                f"Username: {relation.client.username}\n"
                f"Workouts per week: {relation.workouts_per_week}\n"
                f"Goals: {relation.goals or '-'}\n"
                f"Height: {relation.height_cm or '-'} cm\n"
                f"Weight: {relation.weight_kg or '-'} kg\n"
                f"Training location: {relation.training_location or '-'}\n"
                f"Health conditions: {relation.health_conditions or '-'}\n"
                f"Monthly price: {relation.monthly_price or 0:.2f}"
            )
        )

    def show_clients(self, rows):
        relations = []
        self.client_membership_data = {}
        for relation, active_until, missed_count in rows:
            relations.append(relation)
            self.client_membership_data[relation.client.id] = {
                "active_until": active_until,
                "missed_count": missed_count,
            }

        self.client_details.configure(text="Select a client.")
        self.clients_list.set_rows(
            relations,
            "client_id",
            self._format_client,
            self._show_client_details,
        )

    def show_center_rent(self, payment):
        amount = payment.amount if payment else 30000.0
        if payment and payment.rent_status == "active":
            self.center_rent_label.configure(
                text=(
                    f"Fitness center rent is paid until {payment.valid_until} | "
                    f"Amount: {amount:.2f}"
                ),
                text_color="darkgreen",
            )
            self.center_rent_button.configure(text="Rent Paid", state="disabled")
        elif payment:
            self.center_rent_label.configure(
                text=(
                    f"Fitness center rent expired on {payment.valid_until} | "
                    f"Monthly amount: {amount:.2f}"
                ),
                text_color="firebrick",
            )
            self.center_rent_button.configure(
                text=f"Pay monthly rent {amount:.2f}", state="normal"
            )
        else:
            self.center_rent_label.configure(
                text=f"Fitness center rent unpaid | Monthly amount: {amount:.2f}",
                text_color="firebrick",
            )
            self.center_rent_button.configure(
                text=f"Pay monthly rent {amount:.2f}", state="normal"
            )

    def _show_client_details(self, relation):
        self.client_details.configure(
            text=(
                f"Goals: {relation.goals or '-'}\n"
                f"Workouts per week: {relation.workouts_per_week}\n"
                f"Height/Weight: {relation.height_cm or '-'} cm / "
                f"{relation.weight_kg or '-'} kg\n"
                f"Training location: {relation.training_location or '-'}\n"
                f"Health conditions: {relation.health_conditions or '-'}"
            )
        )

    def get_selected_request(self):
        return self.requests_list.selected_row

    def get_selected_client(self):
        return self.clients_list.selected_row

    def get_selected_client_missed_count(self):
        relation = self.get_selected_client()
        if relation is None:
            return 0
        return self.client_membership_data[relation.client.id]["missed_count"]

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")
