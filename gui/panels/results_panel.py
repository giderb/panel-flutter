"""Results visualization panel - placeholder."""

import customtkinter as ctk
from .base_panel import BasePanel

class ResultsPanel(BasePanel):
    def _setup_ui(self):
        placeholder = self.theme_manager.create_styled_label(
            self.frame,
            text="Results Visualization Panel\n(Implementation pending)",
            font=ctk.CTkFont(size=16)
        )
        placeholder.place(relx=0.5, rely=0.5, anchor="center")