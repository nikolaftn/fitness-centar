import customtkinter as ctk


class NotificationView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Notification")
        self.window.geometry("540x280")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.controller.close_notifications)

        ctk.CTkLabel(
            self.window,
            text="Membership Notification",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(22, 14))

        self.message_label = ctk.CTkLabel(
            self.window,
            text="",
            justify="left",
            anchor="w",
            wraplength=480,
        )
        self.message_label.pack(fill="both", expand=True, padx=22, pady=8)

        ctk.CTkButton(
            self.window,
            text="Mark as Read",
            command=self.controller.mark_current_notification_read,
        ).pack(fill="x", padx=18, pady=(8, 18))

    def show_notification(self, notification):
        self.message_label.configure(text=notification.message)

    def close(self):
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
