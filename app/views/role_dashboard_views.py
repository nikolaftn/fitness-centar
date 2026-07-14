import customtkinter as ctk


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def row_text(row, *keys, separator=" | "):
    return separator.join(str(row[key] if row[key] is not None else "") for key in keys)


class ListPanel(ctk.CTkScrollableFrame):
    """Jednostavna lista redova sa izborom, napravljena u CustomTkinter-u."""

    def __init__(self, parent, on_select=None, height=180):
        super().__init__(parent, height=height)
        self.on_select = on_select
        self.rows = []
        self.selected_id = None
        self.selected_row = None
        self.buttons = []

    def set_rows(self, rows, id_key, formatter):
        self.rows = list(rows)
        self.selected_id = None
        self.selected_row = None
        for button in self.buttons:
            button.destroy()
        self.buttons = []
        for row in self.rows:
            button = ctk.CTkButton(
                self,
                text=formatter(row),
                anchor="w",
                fg_color="#e5e7eb",
                text_color="#111827",
                hover_color="#d1d5db",
                command=lambda item=row: self._select(item, id_key),
            )
            button.pack(fill="x", padx=4, pady=4)
            self.buttons.append(button)

    def _select(self, row, id_key):
        self.selected_id = row[id_key]
        self.selected_row = row
        if self.on_select:
            self.on_select()


class ClientDashboardView:
    """CustomTkinter klijentski ekran."""

    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Klijent")
        self.window.geometry("1180x760")
        self.window.minsize(980, 640)
        self.window.grab_set()

        ctk.CTkLabel(
            self.window,
            text=f"Klijent: {user.full_name}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(18, 8))

        self.tabs = ctk.CTkTabview(self.window)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_trainers_tab()
        self._build_workouts_tab()
        self._build_payments_tab()
        self._build_chat_tab()
        self._build_profile_tab(user)

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=24, pady=(0, 12))

    def _build_trainers_tab(self):
        tab = self.tabs.add("Treneri")
        tab.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        ctk.CTkLabel(left, text="Dostupni treneri", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.trainers_list = ListPanel(left, height=240)
        self.trainers_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        form = ctk.CTkFrame(tab)
        form.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        ctk.CTkLabel(form, text="Zahtev za rad sa trenerom", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.request_vars = {}
        fields = (
            ("workouts_per_week", "Treninga nedeljno"),
            ("goals", "Ciljevi"),
            ("height_cm", "Visina cm"),
            ("weight_kg", "Tezina kg"),
            ("training_location", "Lokacija: gym/home/both"),
            ("health_conditions", "Zdravstveni problemi"),
        )
        for key, label in fields:
            self.request_vars[key] = ctk.StringVar(value="gym" if key == "training_location" else "")
            ctk.CTkLabel(form, text=label).pack(anchor="w", padx=12)
            ctk.CTkEntry(form, textvariable=self.request_vars[key]).pack(fill="x", padx=12, pady=(2, 8))
        ctk.CTkButton(form, text="Posalji zahtev", command=self.controller.send_request).pack(fill="x", padx=12, pady=12)

        relations_frame = ctk.CTkFrame(tab)
        relations_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 10))
        ctk.CTkLabel(relations_frame, text="Moji treneri i statusi zahteva", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.relations_list = ListPanel(relations_frame, on_select=self.controller.load_chat, height=140)
        self.relations_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_workouts_tab(self):
        tab = self.tabs.add("Treninzi")
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        ctk.CTkLabel(left, text="Moji treninzi", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.workouts_list = ListPanel(left, on_select=self.controller.load_selected_workout_exercises, height=260)
        self.workouts_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        rating_frame = ctk.CTkFrame(left)
        rating_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.workout_rating_var = ctk.StringVar()
        self.workout_comment_var = ctk.StringVar()
        self.trainer_rating_var = ctk.StringVar()
        self.trainer_comment_var = ctk.StringVar()
        self._entry(rating_frame, "Ocena treninga 1-5", self.workout_rating_var)
        self._entry(rating_frame, "Komentar treninga", self.workout_comment_var)
        self._entry(rating_frame, "Ocena trenera 1-5", self.trainer_rating_var)
        self._entry(rating_frame, "Komentar trenera", self.trainer_comment_var)
        ctk.CTkButton(
            rating_frame,
            text="Sacuvaj ocene treninga i trenera",
            command=self.controller.rate_selected_workout_and_trainer,
        ).pack(fill="x", padx=10, pady=10)

        right = ctk.CTkFrame(tab)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        ctk.CTkLabel(right, text="Vezbe u treningu", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.exercises_list = ListPanel(right, height=220)
        self.exercises_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.exercise_rating_var = ctk.StringVar()
        self.exercise_comment_var = ctk.StringVar()
        self.exercise_video_var = ctk.StringVar()
        self.exercise_video_comment_var = ctk.StringVar()
        self._entry(right, "Ocena vezbe 1-5", self.exercise_rating_var)
        self._entry(right, "Komentar vezbe", self.exercise_comment_var)
        ctk.CTkButton(right, text="Oceni izabranu vezbu", command=self.controller.rate_selected_exercise).pack(fill="x", padx=12, pady=8)
        self._entry(right, "Link/putanja snimka vezbe", self.exercise_video_var)
        self._entry(right, "Komentar uz snimak", self.exercise_video_comment_var)
        ctk.CTkButton(right, text="Posalji snimak treneru", command=self.controller.submit_selected_exercise_video).pack(fill="x", padx=12, pady=8)

    def _build_payments_tab(self):
        tab = self.tabs.add("Placanja")
        ctk.CTkLabel(tab, text="Placanje mesecne pretplate", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=12)
        self.payment_period_var = ctk.StringVar(value="2026-07")
        self._entry(tab, "Period placanja, npr. 2026-07", self.payment_period_var)
        ctk.CTkButton(tab, text="Plati izabranom treneru", command=self.controller.pay_selected_trainer).pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(tab, text="Istorija placanja", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=(18, 8))
        self.payments_list = ListPanel(tab, height=260)
        self.payments_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_chat_tab(self):
        tab = self.tabs.add("Chat")
        ctk.CTkLabel(tab, text="Chat sa izabranim trenerom", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=12)
        self.messages_list = ListPanel(tab, height=360)
        self.messages_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.message_var = ctk.StringVar()
        self._entry(tab, "Poruka", self.message_var)
        ctk.CTkButton(tab, text="Posalji poruku", command=self.controller.send_message).pack(fill="x", padx=12, pady=8)

    def _build_profile_tab(self, user):
        tab = self.tabs.add("Profil")
        self.profile_vars = {
            "first_name": ctk.StringVar(value=user.first_name),
            "last_name": ctk.StringVar(value=user.last_name),
            "birth_date": ctk.StringVar(value=user.birth_date),
        }
        self._entry(tab, "Ime", self.profile_vars["first_name"])
        self._entry(tab, "Prezime", self.profile_vars["last_name"])
        self._entry(tab, "Datum rodjenja GGGG-MM-DD", self.profile_vars["birth_date"])
        ctk.CTkButton(tab, text="Sacuvaj profil", command=self.controller.update_profile).pack(fill="x", padx=12, pady=12)

    def _entry(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=12)
        ctk.CTkEntry(parent, textvariable=variable).pack(fill="x", padx=12, pady=(2, 8))

    def show_trainers(self, trainers):
        self.trainers_list.set_rows(
            trainers,
            "id",
            lambda row: (
                f"{row['first_name']} {row['last_name']} | "
                f"iskustvo {row['years_of_experience']} god. | "
                f"cena {row['price_per_training']:.2f} | "
                f"ocena {row['average_rating'] or 'nema'}"
            ),
        )

    def show_relations(self, relations):
        self.relations_list.set_rows(
            relations,
            "trainer_id",
            lambda row: (
                f"{row['trainer_name']} | {row['status']} | "
                f"{row['workouts_per_week']} nedeljno | "
                f"mesecno {row['monthly_price'] or 0:.2f}"
            ),
        )

    def show_workouts(self, workouts):
        self.workouts_list.set_rows(
            workouts,
            "id",
            lambda row: (
                f"{row['program_name']} / {row['name']} | "
                f"{row['trainer_name']} | {row['status']} | "
                f"trening {row['workout_rating'] or '-'} | trener {row['trainer_rating'] or '-'}"
            ),
        )

    def show_exercises(self, exercises):
        self.exercises_list.set_rows(
            exercises,
            "id",
            lambda row: (
                f"{row['exercise_order']}. {row['name']} | "
                f"ocena {row['rating'] or '-'} | "
                f"tutorial {row['video_url'] or '-'} | "
                f"moj snimak {row['submitted_video'] or '-'}"
            ),
        )

    def show_payments(self, payments):
        self.payments_list.set_rows(
            payments,
            "id",
            lambda row: f"{row['period']} | {row['trainer_name']} | {row['amount']:.2f} | {row['status']}",
        )

    def show_messages(self, messages):
        self.messages_list.set_rows(
            messages,
            "id",
            lambda row: f"{row['created_at']} | {row['sender_username']}: {row['text']}",
        )

    def get_selected_trainer_id(self):
        return self.trainers_list.selected_id

    def get_selected_relation_trainer_id(self):
        row = self.relations_list.selected_row
        if row is None or row["status"] != "accepted":
            return None
        return row["trainer_id"]

    def get_selected_workout_id(self):
        return self.workouts_list.selected_id

    def get_selected_workout_trainer_id(self):
        row = self.workouts_list.selected_row
        return row["trainer_id"] if row else None

    def get_selected_exercise_id(self):
        return self.exercises_list.selected_id

    def get_request_data(self):
        return {key: variable.get().strip() for key, variable in self.request_vars.items()}

    def get_profile_data(self):
        return {key: variable.get().strip() for key, variable in self.profile_vars.items()}

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")


class TrainerDashboardView:
    """CustomTkinter trenerski ekran potreban za klijent tok."""

    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Trener")
        self.window.geometry("1100x700")
        self.window.minsize(940, 600)
        self.window.grab_set()

        ctk.CTkLabel(
            self.window,
            text=f"Trener: {user.full_name}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(18, 8))

        self.tabs = ctk.CTkTabview(self.window)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        self._build_requests_tab()
        self._build_workouts_tab()

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=24, pady=(0, 12))

    def _build_requests_tab(self):
        tab = self.tabs.add("Zahtevi")
        self.requests_list = ListPanel(tab, height=360)
        self.requests_list.pack(fill="both", expand=True, padx=12, pady=12)
        buttons = ctk.CTkFrame(tab)
        buttons.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(buttons, text="Prihvati", command=self.controller.accept_selected_request).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Odbij", fg_color="#6b7280", command=self.controller.reject_selected_request).pack(side="left", padx=8)
        ctk.CTkButton(buttons, text="Osvezi", fg_color="#6b7280", command=self.controller.refresh).pack(side="right")

    def _build_workouts_tab(self):
        tab = self.tabs.add("Treninzi")
        tab.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        ctk.CTkLabel(left, text="Prihvaceni klijenti", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.clients_list = ListPanel(left, height=170)
        self.clients_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.program_name_var = ctk.StringVar()
        self.workout_name_var = ctk.StringVar()
        self.scheduled_date_var = ctk.StringVar()
        self._entry(left, "Naziv programa", self.program_name_var)
        self._entry(left, "Naziv treninga", self.workout_name_var)
        self._entry(left, "Datum treninga opciono", self.scheduled_date_var)
        ctk.CTkButton(left, text="Kreiraj trening", command=self.controller.create_workout).pack(fill="x", padx=12, pady=12)

        right = ctk.CTkFrame(tab)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        ctk.CTkLabel(right, text="Vezbe", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.exercises_list = ListPanel(right, height=170)
        self.exercises_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.exercise_name_var = ctk.StringVar()
        self.exercise_description_var = ctk.StringVar()
        self.exercise_tutorial_var = ctk.StringVar()
        self._entry(right, "Naziv vezbe", self.exercise_name_var)
        self._entry(right, "Opis vezbe", self.exercise_description_var)
        self._entry(right, "Video tutorial link/putanja", self.exercise_tutorial_var)
        ctk.CTkButton(right, text="Dodaj/sacuvaj vezbu", command=self.controller.create_exercise).pack(fill="x", padx=12, pady=12)

    def _entry(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=12)
        ctk.CTkEntry(parent, textvariable=variable).pack(fill="x", padx=12, pady=(2, 8))

    def show_requests(self, requests):
        self.requests_list.set_rows(
            requests,
            "client_id",
            lambda row: (
                f"{row['client_name']} | {row['status']} | "
                f"{row['workouts_per_week']} nedeljno | "
                f"{row['training_location'] or '-'} | {row['goals'] or '-'}"
            ),
        )

    def show_clients(self, clients):
        self.clients_list.set_rows(
            clients,
            "id",
            lambda row: f"{row['client_name']} | {row['username']}",
        )

    def show_exercises(self, exercises):
        self.exercises_list.set_rows(
            exercises,
            "id",
            lambda row: f"{row['name']} | tutorial {row['video_url'] or '-'}",
        )

    def get_selected_request_client_id(self):
        return self.requests_list.selected_id

    def get_selected_client_id(self):
        return self.clients_list.selected_id

    def get_selected_exercise_ids(self):
        return [self.exercises_list.selected_id] if self.exercises_list.selected_id else []

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")
