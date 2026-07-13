import tkinter as tk
from tkinter import messagebox


class LoginView:
    """Prozor za unos podataka za prijavu."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Prijava")
        self.window.geometry("390x250")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        frame = tk.Frame(self.window, padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Korisnicko ime").pack(anchor="w")
        self.username_entry = tk.Entry(frame)
        self.username_entry.pack(fill="x", pady=(4, 14))

        tk.Label(frame, text="Lozinka").pack(anchor="w")
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.pack(fill="x", pady=(4, 18))

        tk.Button(frame, text="Prijavi se", command=self._submit).pack(fill="x")
        self.window.bind("<Return>", lambda _event: self._submit())
        self.username_entry.focus_set()

    def _submit(self):
        self.controller.submit(self.username_entry.get(), self.password_entry.get())

    def show_error(self, message):
        messagebox.showerror("Prijava", message, parent=self.window)

    def show_info(self, message):
        messagebox.showinfo("Prijava", message, parent=self.window)

    def close(self):
        self.window.destroy()
