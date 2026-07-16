import customtkinter as ctk

from app.views.list_panel import ListPanel


class ExerciseManagementView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Upravljanje vezbama")
        self.window.geometry("980x650")
        self.window.minsize(820, 560)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_exercise_management)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Nazad",
            width=90,
            command=self.controller.close_exercise_management,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Vezbe u sistemu",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=(4, 12))
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.exercises_list = ListPanel(content)
        self.exercises_list.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkFrame(content)
        form.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.exercise_id = None
        self.name_entry = self._entry(form, "Naziv")
        self.description_entry = self._entry(form, "Opis")
        self.duration_entry = self._entry(form, "Trajanje u minutima")

        ctk.CTkLabel(form, text="Oprema").pack(anchor="w", padx=14)
        self.equipment_variable = ctk.StringVar(value="Bez opreme")
        self.equipment_menu = ctk.CTkOptionMenu(
            form,
            variable=self.equipment_variable,
            values=["Bez opreme"],
        )
        self.equipment_menu.pack(fill="x", padx=12, pady=(2, 12))

        self.message_label = ctk.CTkLabel(form, text="", anchor="w")
        self.message_label.pack(fill="x", padx=14)

        ctk.CTkButton(
            form,
            text="Nova vezba",
            fg_color="#6b7280",
            command=self.clear_form,
        ).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(
            form,
            text="Sacuvaj vezbu",
            command=self.controller.save_exercise,
        ).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(
            form,
            text="Obrisi vezbu",
            fg_color="#b91c1c",
            command=self.controller.delete_exercise,
        ).pack(fill="x", padx=12, pady=5)

    @staticmethod
    def _entry(parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=14)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=12, pady=(2, 10))
        return entry

    @staticmethod
    def _format_exercise(exercise):
        return (
            f"{exercise.name}\n"
            f"{exercise.duration_minutes or '-'} min | "
            f"oprema: {exercise.equipment_name or 'bez opreme'}"
        )

    def show_exercises(self, exercises):
        self.exercises_list.set_rows(
            exercises,
            "id",
            self._format_exercise,
            self._load_exercise,
        )

    def show_equipment(self, equipment):
        values = ["Bez opreme"]
        values.extend(f"{item.id} | {item.name}" for item in equipment)
        self.equipment_menu.configure(values=values)
        if self.equipment_variable.get() not in values:
            self.equipment_variable.set("Bez opreme")

    def _load_exercise(self, exercise):
        self.clear_form()
        self.exercise_id = exercise.id
        self.name_entry.insert(0, exercise.name)
        self.description_entry.insert(0, exercise.description or "")
        self.duration_entry.insert(0, exercise.duration_minutes or "")
        if exercise.equipment_id is not None:
            self.equipment_variable.set(
                f"{exercise.equipment_id} | {exercise.equipment_name}"
            )

    def clear_form(self):
        self.exercise_id = None
        self.name_entry.delete(0, "end")
        self.description_entry.delete(0, "end")
        self.duration_entry.delete(0, "end")
        self.equipment_variable.set("Bez opreme")

    def get_exercise_data(self):
        equipment = self.equipment_variable.get()
        equipment_id = None
        if equipment != "Bez opreme":
            equipment_id = int(equipment.split(" | ", 1)[0])
        return {
            "id": self.exercise_id,
            "name": self.name_entry.get().strip(),
            "description": self.description_entry.get().strip(),
            "duration_minutes": self.duration_entry.get().strip(),
            "equipment_id": equipment_id,
        }

    def get_selected_exercise_id(self):
        return self.exercises_list.selected_id

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
