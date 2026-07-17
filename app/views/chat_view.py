import customtkinter as ctk


class ChatView:
    def __init__(self, parent, controller, current_user_id, other_user_name):
        self.controller = controller
        self.current_user_id = current_user_id

        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Chat - {other_user_name}")
        self.window.geometry("680x620")
        self.window.minsize(520, 480)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close)

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="Nazad",
            width=90,
            command=self.controller.close,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=other_user_name,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=18)
        ctk.CTkButton(
            header,
            text="Osvezi",
            width=90,
            command=self.controller.refresh,
        ).pack(side="right")

        self.messages_frame = ctk.CTkScrollableFrame(self.window)
        self.messages_frame.pack(fill="both", expand=True, padx=18, pady=8)

        self.error_label = ctk.CTkLabel(
            self.window,
            text="",
            text_color="firebrick",
            anchor="w",
        )
        self.error_label.pack(fill="x", padx=22)

        input_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        input_frame.pack(fill="x", padx=18, pady=(8, 18))
        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Napisite poruku...",
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.message_entry.bind("<Return>", self.controller.send_message)
        ctk.CTkButton(
            input_frame,
            text="Posalji",
            width=100,
            command=self.controller.send_message,
        ).pack(side="right")
        self.message_entry.focus_set()

    def show_messages(self, messages):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()

        for message in messages:
            own_message = message.sender.id == self.current_user_id
            special_message = message.message_type != "text"
            row = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=5)

            sender = "Vi" if own_message else message.sender.username
            if special_message:
                sender = f"{sender} - poslata ocena"
            bubble = ctk.CTkLabel(
                row,
                text=f"{sender}\n{message.text}\n{message.created_at}",
                justify="left",
                anchor="w",
                wraplength=410,
                corner_radius=12,
                padx=14,
                pady=9,
                fg_color=(
                    "#b45309"
                    if special_message
                    else "#2563eb" if own_message else ("gray80", "gray30")
                ),
                text_color="white" if own_message or special_message else ("black", "white"),
            )
            bubble.pack(side="right" if own_message else "left")

        self.window.after(30, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        canvas = getattr(self.messages_frame, "_parent_canvas", None)
        if canvas is not None:
            canvas.yview_moveto(1.0)

    def get_message(self):
        return self.message_entry.get()

    def clear_message(self):
        self.message_entry.delete(0, "end")

    def show_error(self, message):
        self.error_label.configure(text=message)

    def clear_error(self):
        self.error_label.configure(text="")

    def focus(self):
        self.window.lift()
        self.window.focus_force()

    def is_open(self):
        return bool(self.window.winfo_exists())

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
