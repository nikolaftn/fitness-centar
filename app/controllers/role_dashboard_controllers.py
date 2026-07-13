from app.views.role_dashboard_views import (
    ClientDashboardView,
    TrainerDashboardView,
)


class ClientDashboardController:
    """Kontroler pocetnog klijentskog ekrana."""

    def __init__(self, parent, user):
        self.view = ClientDashboardView(parent, user)


class TrainerDashboardController:
    """Kontroler pocetnog trenerskog ekrana."""

    def __init__(self, parent, user):
        self.view = TrainerDashboardView(parent, user)
