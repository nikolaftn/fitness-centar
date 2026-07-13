import tkinter as tk


class BaseRoleDashboardView:
    """Pocetni ekran prijavljenog korisnika dok se moduli dopunjuju."""

    role_title = "Korisnik"
    description = ""

    def __init__(self, parent, user):
        self.window = tk.Toplevel(parent)
        self.window.title(self.role_title)
        self.window.geometry("620x360")
        self.window.minsize(520, 300)

        frame = tk.Frame(self.window, padx=40, pady=40)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=f"Dobrodosli, {user.full_name}",
            font=("Arial", 22, "bold"),
        ).pack(pady=(35, 14))
        tk.Label(frame, text=self.role_title, font=("Arial", 14)).pack()
        tk.Label(
            frame,
            text=self.description,
            wraplength=500,
            justify="center",
        ).pack(pady=(24, 0))


class ClientDashboardView(BaseRoleDashboardView):
    role_title = "Klijentski ekran"
    description = "Ovde ce biti dostupni treneri, zahtevi i programi treninga."


class TrainerDashboardView(BaseRoleDashboardView):
    role_title = "Trenerski ekran"
    description = "Ovde ce biti zahtevi klijenata, programi, vezbe i oprema."
