"""Base panel class for all application panels."""

import customtkinter as ctk
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main_window import MainWindow

class BasePanel(ABC):
    """Base class for all application panels."""

    def __init__(self, parent, main_window: 'MainWindow'):
        self.parent = parent
        self.main_window = main_window
        self.theme_manager = main_window.theme_manager
        self.project_manager = main_window.project_manager
        self.config = main_window.config
        self.logger = main_window.logger

        self.frame = None
        self._create_frame()
        self._setup_ui()

    def _create_frame(self):
        """Create the main frame for this panel."""
        self.frame = self.theme_manager.create_styled_frame(
            self.parent,
            corner_radius=0
        )

    @abstractmethod
    def _setup_ui(self):
        """Setup the user interface for this panel."""
        pass

    def show(self):
        """Show this panel."""
        if self.frame:
            self.frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.on_show()

    def hide(self):
        """Hide this panel."""
        if self.frame:
            self.frame.pack_forget()
        self.on_hide()

    def on_show(self):
        """Called when panel is shown. Override in subclasses."""
        pass

    def on_hide(self):
        """Called when panel is hidden. Override in subclasses."""
        pass

    def refresh(self):
        """Refresh panel with current project data. Override in subclasses."""
        pass

    def create_section_header(self, parent, text: str) -> ctk.CTkLabel:
        """Create a section header label."""
        return self.theme_manager.create_styled_label(
            parent,
            text=text,
            style="subheading",
            font=self.theme_manager.get_heading_font()
        )

    def create_form_field(self, parent, label_text: str, entry_kwargs=None) -> tuple:
        """Create a form field with label and entry."""
        if entry_kwargs is None:
            entry_kwargs = {}

        field_frame = ctk.CTkFrame(parent, fg_color="transparent")

        label = self.theme_manager.create_styled_label(
            field_frame,
            text=label_text,
            font=self.theme_manager.get_body_font()
        )
        label.pack(anchor="w", pady=(0, 5))

        entry = self.theme_manager.create_styled_entry(field_frame, **entry_kwargs)
        entry.pack(fill="x", pady=(0, 10))

        return field_frame, label, entry

    def create_info_card(self, parent, title: str, content: str = "") -> ctk.CTkFrame:
        """Create an information card."""
        card = self.theme_manager.create_styled_frame(parent, elevated=True)

        # Title
        title_label = self.theme_manager.create_styled_label(
            card,
            text=title,
            font=self.theme_manager.get_body_large_font(weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))

        # Content
        if content:
            content_label = self.theme_manager.create_styled_label(
                card,
                text=content,
                font=self.theme_manager.get_body_font(),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            content_label.pack(anchor="w", padx=15, pady=(0, 15))

        return card

    def show_error(self, title: str, message: str):
        """Show an error message."""
        from tkinter import messagebox
        messagebox.showerror(title, message)

    def show_warning(self, title: str, message: str):
        """Show a warning message."""
        from tkinter import messagebox
        messagebox.showwarning(title, message)

    def show_info(self, title: str, message: str):
        """Show an information message."""
        from tkinter import messagebox
        messagebox.showinfo(title, message)