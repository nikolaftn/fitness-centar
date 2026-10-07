import customtkinter as ctk


class ClientRatingsView:
    def __init__(self, parent, client_name, ratings):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Client Ratings")
        self.window.geometry("620x480")
        self.window.minsize(500, 380)
        self.window.transient(parent)
        self.window.grab_set()

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Back",
            width=90,
            command=self.close,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"Ratings for: {client_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)

        content = ctk.CTkScrollableFrame(self.window)
        content.pack(fill="both", expand=True, padx=18, pady=(8, 18))

        if not ratings:
            ctk.CTkLabel(content, text="This client has no trainer ratings yet.").pack(
                anchor="w", padx=10, pady=10
            )
            return

        for rating in ratings:
            card = ctk.CTkFrame(content)
            card.pack(fill="x", padx=6, pady=6)
            ctk.CTkLabel(
                card,
                text=f"Rating: {rating.rating} | Trainer: {rating.trainer.full_name}",
                font=ctk.CTkFont(weight="bold"),
            ).pack(anchor="w", padx=12, pady=(10, 3))
            ctk.CTkLabel(
                card,
                text=rating.comment or "No comment",
                justify="left",
                anchor="w",
                wraplength=520,
            ).pack(fill="x", padx=12, pady=(0, 4))
            ctk.CTkLabel(
                card,
                text=rating.created_at,
                text_color=("gray40", "gray70"),
            ).pack(anchor="w", padx=12, pady=(0, 10))

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()


class ClientRatingView:
    def __init__(self, parent, controller, client_name):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Rate Client")
        self.window.geometry("520x330")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_client_rating)

        ctk.CTkLabel(
            self.window,
            text=f"Rating for: {client_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(20, 14))

        ctk.CTkLabel(self.window, text="Rating (1-5)").pack(anchor="w", padx=22)
        self.rating_entry = ctk.CTkEntry(self.window)
        self.rating_entry.pack(fill="x", padx=18, pady=(2, 10))

        ctk.CTkLabel(self.window, text="Comment visible to trainers").pack(
            anchor="w", padx=22
        )
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
            command=self.controller.close_client_rating,
        ).pack(side="left")
        ctk.CTkButton(
            buttons,
            text="Save Rating",
            command=self.controller.submit_client_rating,
        ).pack(side="right")

    def get_rating(self):
        return self.rating_entry.get(), self.comment_entry.get()

    def show_error(self, message):
        self.message_label.configure(text=message, text_color="firebrick")

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
