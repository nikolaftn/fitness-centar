import customtkinter as ctk

from app.views.list_panel import ListPanel


class EquipmentManagementView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Equipment Management")
        self.window.geometry("900x590")
        self.window.minsize(760, 500)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_equipment_management)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Back",
            width=90,
            command=self.controller.close_equipment_management,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Equipment in the System",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=(4, 12))
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.equipment_list = ListPanel(content)
        self.equipment_list.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkFrame(content)
        form.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.equipment_id = None
        self.name_entry = self._entry(form, "Name")

        ctk.CTkLabel(form, text="Kategorija").pack(anchor="w", padx=14)
        self.category_variable = ctk.StringVar(value="Machine")
        ctk.CTkOptionMenu(
            form,
            variable=self.category_variable,
            values=["Machine", "Prop"],
        ).pack(fill="x", padx=12, pady=(2, 10))

        self.description_entry = self._entry(form, "Description")
        self.message_label = ctk.CTkLabel(form, text="", anchor="w")
        self.message_label.pack(fill="x", padx=14)

        ctk.CTkButton(
            form,
            text="New Equipment",
            fg_color="#6b7280",
            command=self.clear_form,
        ).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(
            form,
            text="Save Equipment",
            command=self.controller.save_equipment,
        ).pack(fill="x", padx=12, pady=5)
        ctk.CTkButton(
            form,
            text="Delete Equipment",
            fg_color="#b91c1c",
            command=self.controller.delete_equipment,
        ).pack(fill="x", padx=12, pady=5)

    @staticmethod
    def _entry(parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=14)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=12, pady=(2, 10))
        return entry

    @staticmethod
    def _format_equipment(equipment):
        category = "Machine" if equipment.category == "machine" else "Prop"
        return f"{equipment.name}\n{category} | {equipment.description or '-'}"

    def show_equipment(self, equipment):
        self.equipment_list.set_rows(
            equipment,
            "id",
            self._format_equipment,
            self._load_equipment,
        )

    def _load_equipment(self, equipment):
        self.clear_form()
        self.equipment_id = equipment.id
        self.name_entry.insert(0, equipment.name)
        self.category_variable.set(
            "Machine" if equipment.category == "machine" else "Prop"
        )
        self.description_entry.insert(0, equipment.description or "")

    def clear_form(self):
        self.equipment_id = None
        self.name_entry.delete(0, "end")
        self.category_variable.set("Machine")
        self.description_entry.delete(0, "end")

    def get_equipment_data(self):
        return {
            "id": self.equipment_id,
            "name": self.name_entry.get().strip(),
            "category": (
                "machine"
                if self.category_variable.get() == "Machine"
                else "prop"
            ),
            "description": self.description_entry.get().strip(),
        }

    def get_selected_equipment_id(self):
        return self.equipment_list.selected_id

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
