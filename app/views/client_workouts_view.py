from datetime import date

import customtkinter as ctk

from app.views.list_panel import ListPanel


class ClientWorkoutsView:
    def __init__(self, parent, controller, trainer_name):
        self.controller = controller
        self.selected_workout = None

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Moji treninzi")
        self.window.geometry("1050x650")
        self.window.minsize(880, 540)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_workouts)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Nazad",
            width=90,
            command=self.controller.close_workouts,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"Treninzi kod trenera: {trainer_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=6)
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            left,
            text="Dodeljeni treninzi",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))
        self.workouts_list = ListPanel(left)
        self.workouts_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        right = ctk.CTkFrame(content)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.workout_title = ctk.CTkLabel(
            right,
            text="Izaberite trening.",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.workout_title.pack(anchor="w", padx=12, pady=(12, 6))
        self.exercises_frame = ctk.CTkScrollableFrame(right)
        self.exercises_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.rate_workout_button = ctk.CTkButton(
            right,
            text="Zavrsi i oceni trening",
            state="disabled",
            command=self.controller.open_workout_rating,
        )
        self.rate_workout_button.pack(fill="x", padx=12, pady=(0, 12))

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=22, pady=(0, 12))

    def _format_workout(self, workout):
        rating = self.workout_ratings.get(workout.id)
        rating_value = rating.rating if rating else None
        return (
            f"{workout.name}\n"
            f"Rok: {workout.scheduled_date} | Status: {workout.status} | "
            f"Ocena: {rating_value or '-'}"
        )

    def show_workouts(self, rows):
        workouts = []
        self.workout_ratings = {}
        for workout, rating in rows:
            workouts.append(workout)
            self.workout_ratings[workout.id] = rating

        self.workouts_list.set_rows(
            workouts,
            "id",
            self._format_workout,
            self._select_workout,
        )

    def _select_workout(self, workout):
        self.selected_workout = workout
        self.workout_title.configure(
            text=f"{workout.name} | Rok: {workout.scheduled_date} | {workout.status}"
        )
        self.controller.load_workout_exercises(workout)

    def show_exercises(self, rows):
        for widget in self.exercises_frame.winfo_children():
            widget.destroy()

        exercises = []
        exercise_ratings = {}
        for exercise, rating in rows:
            exercises.append(exercise)
            exercise_ratings[exercise.id] = rating

        workout = self.selected_workout
        deadline_valid = bool(
            workout and date.fromisoformat(workout.scheduled_date) >= date.today()
        )
        can_change = bool(
            workout and workout.status == "assigned" and deadline_valid
        )
        can_rate = bool(
            workout
            and workout.status in {"assigned", "completed"}
            and deadline_valid
        )

        for exercise in exercises:
            rating = exercise_ratings[exercise.id]
            rating_value = rating.rating if rating else None
            card = ctk.CTkFrame(self.exercises_frame)
            card.pack(fill="x", padx=5, pady=5)
            completed = ctk.BooleanVar(value=exercise.completed)
            checkbox = ctk.CTkCheckBox(
                card,
                text=(
                    f"{exercise.exercise_order}. {exercise.name}\n"
                    f"Serije: {exercise.sets} | "
                    f"Ponavljanja: {exercise.repetitions} | "
                    f"Trajanje: {exercise.duration_minutes} min\n"
                    f"Oprema: {exercise.equipment_name or 'bez opreme'}"
                ),
                variable=completed,
                command=lambda exercise_id=exercise.id, variable=completed: (
                    self.controller.toggle_exercise(exercise_id, variable.get())
                ),
            )
            checkbox.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            if not can_change:
                checkbox.configure(state="disabled")

            rating_button = ctk.CTkButton(
                card,
                text=f"Oceni ({rating_value or '-'})",
                width=110,
                command=lambda current=exercise: self.controller.open_exercise_rating(
                    current
                ),
            )
            rating_button.pack(side="right", padx=10, pady=10)
            if not can_rate or not exercise.completed:
                rating_button.configure(state="disabled")

        if not exercises:
            ctk.CTkLabel(
                self.exercises_frame,
                text="Ovaj trening nema vezbe.",
            ).pack(anchor="w", padx=10, pady=10)

        self.rate_workout_button.configure(
            state="normal" if can_rate else "disabled",
            text=(
                "Azuriraj ocenu treninga"
                if workout and workout.status == "completed"
                else "Zavrsi i oceni trening"
            ),
        )

    def get_selected_workout(self):
        return self.selected_workout

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
