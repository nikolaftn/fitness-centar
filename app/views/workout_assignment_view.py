import customtkinter as ctk


class WorkoutAssignmentView:
    def __init__(self, parent, controller, client_name):
        self.controller = controller
        self.exercise_variables = {}

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Dodela treninga")
        self.window.geometry("700x650")
        self.window.minsize(580, 520)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_workout_assignment)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Nazad",
            width=90,
            command=self.controller.close_workout_assignment,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"Novi trening za: {client_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        self.name_entry = self._entry("Naziv treninga")
        self.deadline_entry = self._entry("Rok za zavrsetak GGGG-MM-DD")

        ctk.CTkLabel(
            self.window,
            text="Izaberite vezbe koje ulaze u trening",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(8, 4))

        self.exercises_frame = ctk.CTkScrollableFrame(self.window, height=300)
        self.exercises_frame.pack(fill="both", expand=True, padx=18, pady=6)

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=22)

        ctk.CTkButton(
            self.window,
            text="Dodeli trening klijentu",
            command=self.controller.submit_workout,
        ).pack(fill="x", padx=18, pady=(8, 18))

    def _entry(self, label):
        ctk.CTkLabel(self.window, text=label).pack(anchor="w", padx=22)
        entry = ctk.CTkEntry(self.window)
        entry.pack(fill="x", padx=18, pady=(2, 8))
        return entry

    def show_exercises(self, exercises):
        for widget in self.exercises_frame.winfo_children():
            widget.destroy()
        self.exercise_variables.clear()

        for exercise in exercises:
            selected = ctk.BooleanVar(value=False)
            self.exercise_variables[exercise.id] = selected
            ctk.CTkCheckBox(
                self.exercises_frame,
                text=(
                    f"{exercise.name} | {exercise.duration_minutes or '-'} min | "
                    f"oprema: {exercise.equipment_name or 'bez opreme'}"
                ),
                variable=selected,
            ).pack(fill="x", padx=8, pady=5, anchor="w")

    def get_workout_data(self):
        return {
            "name": self.name_entry.get().strip(),
            "deadline": self.deadline_entry.get().strip(),
            "exercise_ids": [
                exercise_id
                for exercise_id, selected in self.exercise_variables.items()
                if selected.get()
            ],
        }

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def focus(self):
        self.window.lift()
        self.window.focus_force()

    def is_open(self):
        return bool(self.window.winfo_exists())

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
