import customtkinter as ctk


class ListPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.rows = []
        self.selected_id = None
        self.selected_row = None
        self._buttons = []

    def set_rows(self, rows, id_key, formatter):
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self.rows = list(rows)
        self.selected_id = None
        self.selected_row = None
        for row in self.rows:
            button = ctk.CTkButton(
                self,
                text=formatter(row),
                anchor="w",
                fg_color=("gray85", "gray25"),
                hover_color=("gray75", "gray35"),
                text_color=("black", "white"),
                command=lambda current=row: self._select(current, id_key),
            )
            button.pack(fill="x", padx=4, pady=3)
            self._buttons.append(button)

    def _select(self, row, id_key):
        self.selected_row = row
        self.selected_id = row[id_key]
        for button in self._buttons:
            button.configure(fg_color=("gray85", "gray25"))
        index = self.rows.index(row)
        self._buttons[index].configure(fg_color=("#93c5fd", "#1d4ed8"))


class ClientDashboardView:
    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Klijent")
        self.window.geometry("1180x760")
        self.window.minsize(1000, 650)
        self.window.grab_set()

        ctk.CTkLabel(
            self.window, text=f"Klijent: {user.full_name}",
            font=ctk.CTkFont(size=22, weight="bold")
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

    def _entry(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=12)
        ctk.CTkEntry(parent, textvariable=variable).pack(fill="x", padx=12, pady=(2, 8))

    def _build_trainers_tab(self):
        tab = self.tabs.add("Treneri i zahtevi")
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        ctk.CTkLabel(left, text="Dostupni treneri", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.trainers_list = ListPanel(left, height=260)
        self.trainers_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.request_vars = {
            "workouts_per_week": ctk.StringVar(value="3"),
            "goals": ctk.StringVar(),
            "height_cm": ctk.StringVar(),
            "weight_kg": ctk.StringVar(),
            "training_location": ctk.StringVar(value="gym"),
            "health_conditions": ctk.StringVar(),
        }
        for label, key in [
            ("Broj treninga nedeljno", "workouts_per_week"),
            ("Ciljevi", "goals"),
            ("Visina cm", "height_cm"),
            ("Tezina kg", "weight_kg"),
            ("Lokacija: gym/home/both", "training_location"),
            ("Zdravstveni problemi", "health_conditions"),
        ]:
            self._entry(left, label, self.request_vars[key])
        ctk.CTkButton(left, text="Posalji zahtev treneru", command=self.controller.send_request).pack(fill="x", padx=12, pady=10)

        right = ctk.CTkFrame(tab)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        ctk.CTkLabel(right, text="Moji odnosi sa trenerima", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.relations_list = ListPanel(right, height=520)
        self.relations_list.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkButton(right, text="Osvezi", command=self.controller.refresh).pack(fill="x", padx=12, pady=8)

    def _build_workouts_tab(self):
        tab = self.tabs.add("Treninzi i vezbe")
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        ctk.CTkLabel(left, text="Dodeljeni treninzi", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.workouts_list = ListPanel(left, height=250)
        self.workouts_list.pack(fill="both", expand=True, padx=12, pady=8)
        ctk.CTkButton(left, text="Ucitaj vezbe iz treninga", command=self.controller.load_selected_workout_exercises).pack(fill="x", padx=12, pady=6)

        self.workout_rating_var = ctk.StringVar()
        self.workout_comment_var = ctk.StringVar()
        self.trainer_rating_var = ctk.StringVar()
        self.trainer_comment_var = ctk.StringVar()
        self._entry(left, "Ocena treninga 1-5", self.workout_rating_var)
        self._entry(left, "Komentar treninga", self.workout_comment_var)
        ctk.CTkButton(left, text="Oznaci trening kao odradjen i oceni", command=self.controller.rate_selected_workout).pack(fill="x", padx=12, pady=6)
        self._entry(left, "Jednokratna ocena trenera 1-5", self.trainer_rating_var)
        self._entry(left, "Komentar trenera", self.trainer_comment_var)
        ctk.CTkButton(left, text="Oceni trenera jednom", command=self.controller.rate_selected_trainer).pack(fill="x", padx=12, pady=6)

        right = ctk.CTkFrame(tab)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        ctk.CTkLabel(right, text="Vezbe u treningu", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.exercises_list = ListPanel(right, height=260)
        self.exercises_list.pack(fill="both", expand=True, padx=12, pady=8)
        self.exercise_rating_var = ctk.StringVar()
        self.exercise_comment_var = ctk.StringVar()
        self.exercise_video_var = ctk.StringVar()
        self.exercise_video_comment_var = ctk.StringVar()
        self._entry(right, "Ocena vezbe 1-5", self.exercise_rating_var)
        self._entry(right, "Komentar vezbe", self.exercise_comment_var)
        ctk.CTkButton(right, text="Oceni vezbu", command=self.controller.rate_selected_exercise).pack(fill="x", padx=12, pady=6)
        self._entry(right, "Link ili putanja mog snimka", self.exercise_video_var)
        self._entry(right, "Komentar uz snimak", self.exercise_video_comment_var)
        ctk.CTkButton(right, text="Posalji snimak treneru", command=self.controller.submit_selected_exercise_video).pack(fill="x", padx=12, pady=6)

    def _build_payments_tab(self):
        tab = self.tabs.add("Placanja")
        self.payment_period_var = ctk.StringVar(value="2026-07")
        self._entry(tab, "Period placanja, npr. 2026-07", self.payment_period_var)
        ctk.CTkButton(tab, text="Plati izabranom prihvacenom treneru", command=self.controller.pay_selected_trainer).pack(fill="x", padx=12, pady=8)
        self.payments_list = ListPanel(tab, height=400)
        self.payments_list.pack(fill="both", expand=True, padx=12, pady=12)

    def _build_chat_tab(self):
        tab = self.tabs.add("Chat")
        ctk.CTkLabel(tab, text="U kartici Treneri izaberi prihvacenog trenera.").pack(anchor="w", padx=12, pady=8)
        self.messages_list = ListPanel(tab, height=420)
        self.messages_list.pack(fill="both", expand=True, padx=12, pady=8)
        self.message_var = ctk.StringVar()
        self._entry(tab, "Poruka", self.message_var)
        row = ctk.CTkFrame(tab)
        row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="Ucitaj chat", command=self.controller.load_chat).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Posalji", command=self.controller.send_message).pack(side="left", padx=4)

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

    def show_trainers(self, rows):
        self.trainers_list.set_rows(rows, "id", lambda r: f"{r['first_name']} {r['last_name']} | {r['education'] or '-'} | iskustvo {r['years_of_experience']} | cena {r['price_per_training']:.2f} | ocena {r['average_rating'] or 'nema'} ({r['rating_count']})")

    def show_relations(self, rows):
        self.relations_list.set_rows(rows, "trainer_id", lambda r: f"{r['trainer_name']} | {r['status']} | {r['workouts_per_week']} nedeljno | mesecno {r['monthly_price'] or 0:.2f}")

    def show_workouts(self, rows):
        self.workouts_list.set_rows(rows, "id", lambda r: f"{r['program_name']} / {r['name']} | {r['trainer_name']} | {r['scheduled_date'] or '-'} | {r['status']} | ocena {r['workout_rating'] or '-'}")

    def show_exercises(self, rows):
        self.exercises_list.set_rows(rows, "id", lambda r: f"{r['exercise_order']}. {r['name']} | {r['duration_minutes'] or '-'} min | tutorial {r['video_url'] or '-'} | ocena {r['rating'] or '-'} | moj snimak {r['submitted_video'] or '-'}")

    def show_payments(self, rows):
        self.payments_list.set_rows(rows, "id", lambda r: f"{r['period']} | {r['trainer_name']} | {r['amount']:.2f} | {r['status']}")

    def show_messages(self, rows):
        self.messages_list.set_rows(rows, "id", lambda r: f"{r['created_at']} | {r['sender_username']}: {r['text']}")

    def get_selected_trainer_id(self): return self.trainers_list.selected_id
    def get_selected_workout_id(self): return self.workouts_list.selected_id
    def get_selected_exercise_id(self): return self.exercises_list.selected_id
    def get_selected_workout_trainer_id(self):
        return self.workouts_list.selected_row["trainer_id"] if self.workouts_list.selected_row else None
    def get_selected_relation_trainer_id(self):
        row = self.relations_list.selected_row
        return row["trainer_id"] if row and row["status"] == "accepted" else None
    def get_request_data(self): return {k: v.get().strip() for k, v in self.request_vars.items()}
    def get_profile_data(self): return {k: v.get().strip() for k, v in self.profile_vars.items()}
    def show_error(self, message): self.message_label.configure(text=message, text_color="firebrick")
    def show_info(self, message): self.message_label.configure(text=message, text_color="darkgreen")


class TrainerDashboardView:
    def __init__(self, parent, controller, user):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Trener")
        self.window.geometry("1240x790")
        self.window.minsize(1050, 680)
        self.window.grab_set()

        ctk.CTkLabel(self.window, text=f"Trener: {user.full_name}", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=24, pady=(18, 8))
        self.tabs = ctk.CTkTabview(self.window)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        self._build_profile_tab()
        self._build_requests_clients_tab()
        self._build_programs_tab()
        self._build_exercises_tab()
        self._build_equipment_tab()
        self._build_ratings_submissions_tab()
        self._build_chat_tab()
        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=24, pady=(0, 12))

    def _entry(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=12)
        ctk.CTkEntry(parent, textvariable=variable).pack(fill="x", padx=12, pady=(2, 8))

    def _build_profile_tab(self):
        tab = self.tabs.add("Moj profil")
        self.profile_vars = {key: ctk.StringVar() for key in ["first_name", "last_name", "birth_date", "education", "diploma_license", "biography", "years_of_experience", "price_per_training"]}
        for label, key in [("Ime", "first_name"), ("Prezime", "last_name"), ("Datum rodjenja GGGG-MM-DD", "birth_date"), ("Skolovanje", "education"), ("Diploma/licenca", "diploma_license"), ("Biografija/dodatni podaci", "biography"), ("Godine iskustva", "years_of_experience"), ("Cena jednog treninga", "price_per_training")]:
            self._entry(tab, label, self.profile_vars[key])
        ctk.CTkButton(tab, text="Sacuvaj profil i preracunaj mesecne cene", command=self.controller.save_profile).pack(fill="x", padx=12, pady=12)

    def _build_requests_clients_tab(self):
        tab = self.tabs.add("Klijenti")
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(tab); left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        ctk.CTkLabel(left, text="Zahtevi klijenata", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.requests_list = ListPanel(left, height=480); self.requests_list.pack(fill="both", expand=True, padx=12, pady=8)
        row = ctk.CTkFrame(left); row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="Prihvati", command=self.controller.accept_selected_request).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Odbij", fg_color="#6b7280", command=self.controller.reject_selected_request).pack(side="left", padx=4)
        right = ctk.CTkFrame(tab); right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        ctk.CTkLabel(right, text="Prihvaceni klijenti i izvestaji", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.clients_list = ListPanel(right, height=480); self.clients_list.pack(fill="both", expand=True, padx=12, pady=8)
        self.client_rating_var = ctk.StringVar(); self.client_rating_comment_var = ctk.StringVar()
        self._entry(right, "Interna ocena klijenta 1-5", self.client_rating_var)
        self._entry(right, "Komentar koji vide samo treneri", self.client_rating_comment_var)
        ctk.CTkButton(right, text="Sacuvaj internu ocenu", command=self.controller.save_client_rating).pack(fill="x", padx=12, pady=8)

    def _build_programs_tab(self):
        tab = self.tabs.add("Programi i treninzi")
        tab.grid_columnconfigure((0, 1), weight=1); tab.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(tab); left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        ctk.CTkLabel(left, text="Kreiranje programa za izabranog klijenta", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.program_name_var = ctk.StringVar(); self.program_description_var = ctk.StringVar(); self.workout_name_var = ctk.StringVar(); self.scheduled_date_var = ctk.StringVar()
        for label, var in [("Naziv programa", self.program_name_var), ("Opis programa", self.program_description_var), ("Naziv treninga", self.workout_name_var), ("Datum treninga opciono", self.scheduled_date_var)]: self._entry(left, label, var)
        ctk.CTkLabel(left, text="Izaberi vezbu u kartici Vezbe. Za vise vezbi koristi Ctrl klik u nastavku nije potreban; trenutna verzija dodaje izabranu vezbu.", wraplength=430).pack(anchor="w", padx=12, pady=8)
        ctk.CTkButton(left, text="Kreiraj program i trening", command=self.controller.create_workout).pack(fill="x", padx=12, pady=8)
        right = ctk.CTkFrame(tab); right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        ctk.CTkLabel(right, text="Moji treninzi", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.workouts_list = ListPanel(right, height=430); self.workouts_list.pack(fill="both", expand=True, padx=12, pady=8)
        ctk.CTkButton(right, text="Kopiraj izabrani program izabranom klijentu", command=self.controller.copy_selected_program).pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(right, text="Oznaci trening kao neodradjen", fg_color="#b45309", command=self.controller.mark_workout_missed).pack(fill="x", padx=12, pady=6)

    def _build_exercises_tab(self):
        tab = self.tabs.add("Vezbe")
        tab.grid_columnconfigure((0, 1), weight=1); tab.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(tab); left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        self.exercises_list = ListPanel(left, height=560); self.exercises_list.pack(fill="both", expand=True, padx=12, pady=12)
        right = ctk.CTkFrame(tab); right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        self.exercise_id_var = ctk.StringVar(); self.exercise_name_var = ctk.StringVar(); self.exercise_description_var = ctk.StringVar(); self.exercise_tutorial_var = ctk.StringVar(); self.exercise_duration_var = ctk.StringVar()
        for label, var in [("Naziv", self.exercise_name_var), ("Opis", self.exercise_description_var), ("Video tutorial link/putanja", self.exercise_tutorial_var), ("Trajanje u minutima", self.exercise_duration_var)]: self._entry(right, label, var)
        ctk.CTkButton(right, text="Ucitaj izabranu vezbu u formu", command=self._load_selected_exercise).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(right, text="Nova/cista forma", fg_color="#6b7280", command=self.clear_exercise_form).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(right, text="Sacuvaj vezbu", command=self.controller.save_exercise).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(right, text="Obrisi vezbu", fg_color="#b91c1c", command=self.controller.delete_exercise).pack(fill="x", padx=12, pady=5)

    def _build_equipment_tab(self):
        tab = self.tabs.add("Oprema")
        tab.grid_columnconfigure((0, 1), weight=1); tab.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(tab); left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        self.equipment_list = ListPanel(left, height=560); self.equipment_list.pack(fill="both", expand=True, padx=12, pady=12)
        right = ctk.CTkFrame(tab); right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        self.equipment_id_var = ctk.StringVar(); self.equipment_name_var = ctk.StringVar(); self.equipment_category_var = ctk.StringVar(value="machine"); self.equipment_description_var = ctk.StringVar()
        for label, var in [("Naziv", self.equipment_name_var), ("Kategorija machine/prop", self.equipment_category_var), ("Opis", self.equipment_description_var)]: self._entry(right, label, var)
        ctk.CTkButton(right, text="Ucitaj izabranu opremu", command=self._load_selected_equipment).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(right, text="Nova/cista forma", fg_color="#6b7280", command=self.clear_equipment_form).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(right, text="Sacuvaj opremu", command=self.controller.save_equipment).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(right, text="Obrisi opremu", fg_color="#b91c1c", command=self.controller.delete_equipment).pack(fill="x", padx=12, pady=5)

    def _build_ratings_submissions_tab(self):
        tab = self.tabs.add("Ocene i snimci")
        tab.grid_columnconfigure((0, 1), weight=1); tab.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(tab); left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        ctk.CTkLabel(left, text="Interne ocene klijenata - vide samo treneri", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.client_ratings_list = ListPanel(left, height=520); self.client_ratings_list.pack(fill="both", expand=True, padx=12, pady=8)
        right = ctk.CTkFrame(tab); right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=10)
        ctk.CTkLabel(right, text="Snimci vezbanja koje su poslali klijenti", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=10)
        self.submissions_list = ListPanel(right, height=520); self.submissions_list.pack(fill="both", expand=True, padx=12, pady=8)

    def _build_chat_tab(self):
        tab = self.tabs.add("Chat")
        ctk.CTkLabel(tab, text="Izaberi prihvacenog klijenta u kartici Klijenti.").pack(anchor="w", padx=12, pady=8)
        self.messages_list = ListPanel(tab, height=430); self.messages_list.pack(fill="both", expand=True, padx=12, pady=8)
        self.message_var = ctk.StringVar(); self._entry(tab, "Poruka", self.message_var)
        row = ctk.CTkFrame(tab); row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="Ucitaj chat", command=self.controller.load_chat).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Posalji", command=self.controller.send_message).pack(side="left", padx=4)

    def show_profile(self, row):
        if not row: return
        for key in self.profile_vars: self.profile_vars[key].set("" if row[key] is None else str(row[key]))
    def show_requests(self, rows): self.requests_list.set_rows(rows, "client_id", lambda r: f"{r['client_name']} | {r['status']} | {r['workouts_per_week']}x nedeljno | cilj: {r['goals'] or '-'} | {r['height_cm'] or '-'}cm/{r['weight_kg'] or '-'}kg | {r['training_location'] or '-'} | zdravlje: {r['health_conditions'] or '-'}")
    def show_clients(self, rows): self.clients_list.set_rows(rows, "id", lambda r: f"{r['client_name']} | {r['username']} | {r['workouts_per_week']}x | cena {r['monthly_price']:.2f} | propusteno {r['missed_count']} | cilj {r['goals'] or '-'} | zdravlje {r['health_conditions'] or '-'}")
    def show_exercises(self, rows): self.exercises_list.set_rows(rows, "id", lambda r: f"{r['name']} | {r['duration_minutes'] or '-'} min | tutorial {r['video_url'] or '-'} | {r['description'] or '-'}")
    def show_equipment(self, rows): self.equipment_list.set_rows(rows, "id", lambda r: f"{r['name']} | {r['category']} | {r['description'] or '-'}")
    def show_workouts(self, rows): self.workouts_list.set_rows(rows, "id", lambda r: f"{r['program_name']} / {r['name']} | {r['client_name']} | {r['scheduled_date'] or '-'} | {r['status']}")
    def show_submissions(self, rows): self.submissions_list.set_rows(rows, "id", lambda r: f"{r['client_name']} | {r['workout_name']} / {r['exercise_name']} | {r['video_url']} | {r['comment'] or '-'}")
    def show_client_ratings(self, rows): self.client_ratings_list.set_rows(rows, "client_id", lambda r: f"{r['client_name']} | ocena {r['rating']} | trener {r['trainer_name']} | {r['comment'] or '-'}")
    def show_messages(self, rows): self.messages_list.set_rows(rows, "id", lambda r: f"{r['created_at']} | {r['sender_username']}: {r['text']}")

    def _load_selected_exercise(self):
        row = self.exercises_list.selected_row
        if not row: return
        self.exercise_id_var.set(str(row["id"])); self.exercise_name_var.set(row["name"]); self.exercise_description_var.set(row["description"] or ""); self.exercise_tutorial_var.set(row["video_url"] or ""); self.exercise_duration_var.set(row["duration_minutes"] or "")
    def clear_exercise_form(self):
        for var in [self.exercise_id_var, self.exercise_name_var, self.exercise_description_var, self.exercise_tutorial_var, self.exercise_duration_var]: var.set("")
    def _load_selected_equipment(self):
        row = self.equipment_list.selected_row
        if not row: return
        self.equipment_id_var.set(str(row["id"])); self.equipment_name_var.set(row["name"]); self.equipment_category_var.set(row["category"]); self.equipment_description_var.set(row["description"] or "")
    def clear_equipment_form(self):
        self.equipment_id_var.set(""); self.equipment_name_var.set(""); self.equipment_category_var.set("machine"); self.equipment_description_var.set("")

    def get_selected_request_client_id(self): return self.requests_list.selected_id
    def get_selected_client_id(self): return self.clients_list.selected_id
    def get_selected_exercise_id(self): return self.exercises_list.selected_id
    def get_selected_exercise_ids(self): return [self.exercises_list.selected_id] if self.exercises_list.selected_id else []
    def get_selected_equipment_id(self): return self.equipment_list.selected_id
    def get_selected_trainer_workout_id(self): return self.workouts_list.selected_id
    def get_selected_trainer_workout(self): return self.workouts_list.selected_row
    def get_trainer_profile_data(self): return {k: v.get().strip() for k, v in self.profile_vars.items()}
    def get_exercise_data(self): return {"id": int(self.exercise_id_var.get()) if self.exercise_id_var.get() else None, "name": self.exercise_name_var.get().strip(), "description": self.exercise_description_var.get().strip(), "video_url": self.exercise_tutorial_var.get().strip(), "duration_minutes": self.exercise_duration_var.get().strip()}
    def get_equipment_data(self): return {"id": int(self.equipment_id_var.get()) if self.equipment_id_var.get() else None, "name": self.equipment_name_var.get().strip(), "category": self.equipment_category_var.get().strip(), "description": self.equipment_description_var.get().strip()}
    def show_error(self, message): self.message_label.configure(text=message, text_color="firebrick")
    def show_info(self, message): self.message_label.configure(text=message, text_color="darkgreen")
