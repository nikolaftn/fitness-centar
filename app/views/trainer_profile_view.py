import customtkinter as ctk


class TrainerProfileView:
    def __init__(self, parent, controller, profile):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Trainer Profile")
        self.window.geometry("650x650")
        self.window.minsize(540, 560)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_profile)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Back",
            width=90,
            command=self.controller.close_profile,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="My Profile",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        self.entries = {}
        fields = [
            ("first_name", "First name"),
            ("last_name", "Last name"),
            ("birth_date", "Date of birth YYYY-MM-DD"),
            ("education", "Education"),
            ("diploma_license", "Diploma or license"),
            ("biography", "Biography and additional details"),
            ("years_of_experience", "Years of experience"),
            ("price_per_training", "Price per session"),
        ]
        for key, label in fields:
            ctk.CTkLabel(self.window, text=label).pack(anchor="w", padx=22)
            entry = ctk.CTkEntry(self.window)
            entry.pack(fill="x", padx=18, pady=(2, 8))
            value = getattr(profile, key)
            entry.insert(0, "" if value is None else str(value))
            self.entries[key] = entry

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=22)
        ctk.CTkButton(
            self.window,
            text="Save profile",
            command=self.controller.save_profile,
        ).pack(fill="x", padx=18, pady=(8, 18))

    def get_profile_data(self):
        return {key: entry.get().strip() for key, entry in self.entries.items()}

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def show_info(self, message):
        self.message_label.configure(text=message, text_color="darkgreen")

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
