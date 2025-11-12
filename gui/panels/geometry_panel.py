"""Geometry definition panel - placeholder for remaining panels."""

import customtkinter as ctk
from .base_panel import BasePanel

class GeometryPanel(BasePanel):
    def _setup_ui(self):
        placeholder = self.theme_manager.create_styled_label(
            self.frame,
            text="Geometry Panel\n(Implementation pending)",
            font=self.theme_manager.get_heading_font()
        )
        placeholder.place(relx=0.5, rely=0.5, anchor="center")