import customtkinter as ctk


class ListPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.rows = []
        self.selected_id = None
        self.selected_row = None
        self._buttons = []

    @staticmethod
    def _value(row, key):
        return getattr(row, key) if hasattr(row, key) else row[key]

    def set_rows(self, rows, id_key, formatter, on_select=None):
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        self.rows = list(rows)
        self.selected_id = None
        self.selected_row = None
        self.on_select = on_select
        for row in self.rows:
            button = ctk.CTkButton(
                self,
                text=formatter(row),
                anchor="w",
                fg_color=("gray85", "gray25"),
                hover_color=("gray75", "gray35"),
                text_color=("black", "white"),
                command=lambda current=row: self._select(current, id_key),
            )
            button.pack(fill="x", padx=4, pady=3)
            self._buttons.append(button)

    def _select(self, row, id_key):
        self.selected_row = row
        self.selected_id = self._value(row, id_key)
        for button in self._buttons:
            button.configure(fg_color=("gray85", "gray25"))
        index = self.rows.index(row)
        self._buttons[index].configure(fg_color=("#93c5fd", "#1d4ed8"))
        if self.on_select:
            self.on_select(row)
