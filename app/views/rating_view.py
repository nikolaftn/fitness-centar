import customtkinter as ctk


class RatingView:
    def __init__(self, parent, title, on_submit, on_close):
        self.on_submit = on_submit
        self.on_close = on_close

        self.window = ctk.CTkToplevel(parent)
        self.window.title(title)
        self.window.geometry("520x330")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        ctk.CTkLabel(
            self.window,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(20, 14))

        ctk.CTkLabel(self.window, text="Rating (1-5)").pack(anchor="w", padx=22)
        self.rating_entry = ctk.CTkEntry(self.window)
        self.rating_entry.pack(fill="x", padx=18, pady=(2, 10))

        ctk.CTkLabel(self.window, text="Comment").pack(anchor="w", padx=22)
        self.comment_entry = ctk.CTkEntry(self.window)
        self.comment_entry.pack(fill="x", padx=18, pady=(2, 10))

        self.message_label = ctk.CTkLabel(self.window, text="", anchor="w")
        self.message_label.pack(fill="x", padx=22)

        buttons = ctk.CTkFrame(self.window, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(8, 18))
        ctk.CTkButton(
            buttons,
            text="Back",
            fg_color="#6b7280",
            command=self.on_close,
        ).pack(side="left")
        ctk.CTkButton(
            buttons,
            text="Save Rating",
            command=self.on_submit,
        ).pack(side="right")

    def get_data(self):
        return self.rating_entry.get(), self.comment_entry.get()

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
