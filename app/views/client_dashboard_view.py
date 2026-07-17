import customtkinter as ctk

from app.views.list_panel import ListPanel


class ClientDashboardView:
    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Klijent")
        self.window.geometry("1280x760")
        self.window.minsize(1100, 680)
        self.window.grab_set()

        self._build_header(user)
        self._build_content()

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=24, pady=(0, 14))

    def _build_header(self, user):
        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 8))
        ctk.CTkLabel(
            header,
            text=f"Klijent: {user.full_name}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="Osvezi",
            width=90,
            command=self.controller.refresh,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header,
            text="Moj profil",
            width=110,
            command=self.controller.open_profile,
        ).pack(side="right")

    def _build_content(self):
        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)
        self._build_available_trainers(content)
        self._build_relations(content)

    def _build_available_trainers(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            panel,
            text="Dostupni treneri",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(14, 8))
        self.trainers_list = ListPanel(panel, height=190)
        self.trainers_list.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        self.trainer_details = ctk.CTkLabel(
            panel,
            text="Izaberite trenera.",
            justify="left",
            anchor="w",
            wraplength=520,
        )
        self.trainer_details.pack(fill="x", padx=14, pady=(0, 8))

        self.request_entries = {}
        fields = [
            ("workouts_per_week", "Treninzi nedeljno", "3"),
            ("goals", "Ciljevi", ""),
            ("height_cm", "Visina u cm", ""),
            ("weight_kg", "Tezina u kg", ""),
            ("health_conditions", "Zdravstveni problemi", ""),
        ]
        for key, label, value in fields:
            self.request_entries[key] = self._entry(panel, label, value)

        ctk.CTkLabel(panel, text="Mesto treninga").pack(anchor="w", padx=14)
        self.location_variable = ctk.StringVar(value="gym")
        ctk.CTkOptionMenu(
            panel,
            variable=self.location_variable,
            values=["gym", "home", "both"],
        ).pack(fill="x", padx=12, pady=(2, 8))

        ctk.CTkButton(
            panel,
            text="Posalji zahtev izabranom treneru",
            command=self.controller.send_request,
        ).pack(fill="x", padx=12, pady=(4, 14))

    def _build_relations(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            panel,
            text="Moji treneri i zahtevi",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(14, 8))
        self.relations_list = ListPanel(panel, height=400)
        self.relations_list.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.relation_details = ctk.CTkLabel(
            panel,
            text="Izaberite odnos sa trenerom.",
            justify="left",
            anchor="w",
            wraplength=520,
        )
        self.relation_details.pack(fill="x", padx=14, pady=(0, 10))

        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 6))
        self.workouts_button = ctk.CTkButton(
            row,
            text="Otvori treninge",
            command=self.controller.open_workouts,
        )
        self.workouts_button.pack(side="left", fill="x", expand=True, padx=4)
        self.chat_button = ctk.CTkButton(
            row,
            text="Otvori chat",
            command=self.controller.open_chat,
        )
        self.chat_button.pack(side="left", fill="x", expand=True, padx=4)

        self.pay_button = ctk.CTkButton(
            panel,
            text="Plati mesecnu clanarinu",
            command=self.controller.pay_membership,
        )
        self.pay_button.pack(fill="x", padx=14, pady=(0, 6))
        self.rate_trainer_button = ctk.CTkButton(
            panel,
            text="Oceni trenera",
            command=self.controller.open_trainer_rating,
        )
        self.rate_trainer_button.pack(fill="x", padx=14, pady=(0, 14))
        self._set_relation_actions(None)

    @staticmethod
    def _entry(parent, label, value):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=14)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=12, pady=(2, 6))
        if value:
            entry.insert(0, value)
        return entry

    def _format_trainer(self, profile):
        average_rating = self.trainer_average_ratings[profile.user.id]
        return (
            f"{profile.full_name}\n"
            f"Cena treninga: {profile.price_per_training:.2f} | "
            f"Ocena: {average_rating or 'nema'}"
        )

    @staticmethod
    def _relation_state(relation):
        if relation.status == "pending":
            return "Zahtev ceka odgovor trenera"
        if relation.is_paid:
            return f"Clanarina aktivna do {relation.expiration_date}"
        return "Zahtev prihvacen - clanarina nije aktivna"

    def show_trainers(self, rows):
        profiles = []
        self.trainer_average_ratings = {}
        for profile, average_rating, rating_count in rows:
            profiles.append(profile)
            self.trainer_average_ratings[profile.user.id] = average_rating

        self.trainer_details.configure(text="Izaberite trenera.")
        self.trainers_list.set_rows(
            profiles,
            "user_id",
            self._format_trainer,
            self._show_trainer_details,
        )

    def _show_trainer_details(self, profile):
        self.trainer_details.configure(
            text=(
                f"Skolovanje: {profile.education or '-'}\n"
                f"Iskustvo: {profile.years_of_experience} godina\n"
                f"Biografija: {profile.biography or '-'}"
            )
        )

    def show_relations(self, rows):
        self.relation_details.configure(text="Izaberite odnos sa trenerom.")
        self._set_relation_actions(None)
        self.relations_list.set_rows(
            rows,
            "trainer_id",
            self._format_relation,
            self._show_relation_details,
        )

    def _format_relation(self, relation):
        return f"{relation.trainer_name}\n{self._relation_state(relation)}"

    def _show_relation_details(self, relation):
        self.relation_details.configure(
            text=(
                f"{self._relation_state(relation)}\n"
                f"Mesecna cena: {relation.monthly_price or 0:.2f}\n"
                f"Treninzi nedeljno: {relation.workouts_per_week}\n"
                f"Ciljevi: {relation.goals or '-'}"
            )
        )
        self._set_relation_actions(relation)

    def _set_relation_actions(self, relation):
        active = bool(relation and relation.status == "accepted" and relation.is_paid)
        can_pay = bool(relation and relation.status == "accepted" and not relation.is_paid)
        active_state = "normal" if active else "disabled"
        self.workouts_button.configure(state=active_state)
        self.chat_button.configure(state=active_state)
        self.rate_trainer_button.configure(state=active_state)
        self.pay_button.configure(state="normal" if can_pay else "disabled")
        if can_pay:
            self.pay_button.configure(
                text=f"Plati mesecnu clanarinu {relation.monthly_price or 0:.2f}"
            )
        else:
            self.pay_button.configure(text="Plati mesecnu clanarinu")

    def get_selected_trainer(self):
        return self.trainers_list.selected_row

    def get_selected_relation(self):
        return self.relations_list.selected_row

    def get_request_data(self):
        data = {
            key: entry.get().strip()
            for key, entry in self.request_entries.items()
        }
        data["training_location"] = self.location_variable.get()
        return data

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")
