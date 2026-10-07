import customtkinter as ctk


class WorkoutAssignmentView:
    def __init__(self, parent, controller, client_name):
        self.controller = controller
        self.exercise_variables = {}
        self.exercise_entries = {}

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Workout Assignment")
        self.window.geometry("820x700")
        self.window.minsize(700, 580)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_workout_assignment)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Back",
            width=90,
            command=self.controller.close_workout_assignment,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"New workout for: {client_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        self.name_entry = self._entry("Workout Name")
        self.deadline_entry = self._entry("Completion Deadline YYYY-MM-DD")

        ctk.CTkLabel(
            self.window,
            text="Select Exercises for This Workout",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(8, 4))

        self.exercises_frame = ctk.CTkScrollableFrame(self.window, height=300)
        self.exercises_frame.pack(fill="both", expand=True, padx=18, pady=6)

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=22)

        ctk.CTkButton(
            self.window,
            text="Assign Workout to Client",
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
        self.exercise_entries.clear()

        for exercise in exercises:
            card = ctk.CTkFrame(self.exercises_frame)
            card.pack(fill="x", padx=6, pady=6)

            selected = ctk.BooleanVar(value=False)
            self.exercise_variables[exercise.id] = selected
            ctk.CTkCheckBox(
                card,
                text=(
                    f"{exercise.name} | {exercise.duration_minutes or '-'} min | "
                    f"Equipment: {exercise.equipment_name or 'no equipment'}"
                ),
                variable=selected,
            ).pack(fill="x", padx=10, pady=(10, 6), anchor="w")

            values = ctk.CTkFrame(card, fg_color="transparent")
            values.pack(fill="x", padx=8, pady=(0, 10))
            values.grid_columnconfigure((0, 1, 2), weight=1)

            sets_entry = self._exercise_number_entry(values, 0, "Number of sets", "3")
            repetitions_entry = self._exercise_number_entry(
                values, 1, "Repetitions", "10"
            )
            duration_entry = self._exercise_number_entry(
                values,
                2,
                "Duration (minutes)",
                str(exercise.duration_minutes or 10),
            )
            self.exercise_entries[exercise.id] = {
                "sets": sets_entry,
                "repetitions": repetitions_entry,
                "duration_minutes": duration_entry,
            }

    @staticmethod
    def _exercise_number_entry(parent, column, label, default_value):
        field = ctk.CTkFrame(parent, fg_color="transparent")
        field.grid(row=0, column=column, sticky="ew", padx=4)
        ctk.CTkLabel(field, text=label).pack(anchor="w")
        entry = ctk.CTkEntry(field)
        entry.pack(fill="x", pady=(2, 0))
        entry.insert(0, default_value)
        return entry

    def get_workout_data(self):
        assignments = []
        for exercise_id, selected in self.exercise_variables.items():
            if not selected.get():
                continue
            entries = self.exercise_entries[exercise_id]
            assignments.append(
                {
                    "exercise_id": exercise_id,
                    "sets": entries["sets"].get().strip(),
                    "repetitions": entries["repetitions"].get().strip(),
                    "duration_minutes": entries["duration_minutes"].get().strip(),
                }
            )
        return {
            "name": self.name_entry.get().strip(),
            "deadline": self.deadline_entry.get().strip(),
            "exercise_assignments": assignments,
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
