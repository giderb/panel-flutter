"""Theme and styling management for the GUI."""

import os
import sys
import customtkinter as ctk
from typing import Dict, Tuple

class ThemeManager:
    """Manages application themes and styling."""

    def __init__(self):
        self.current_theme = "dark"
        self.current_color = "blue"
        self._setup_colors()

    def _setup_colors(self):
        """Setup color schemes for different themes."""
        self.colors = {
            "dark": {
                "primary": "#1f538d",
                "secondary": "#14375e",
                "accent": "#2fa572",
                "background": "#212121",
                "surface": "#2b2b2b",
                "text": "#ffffff",
                "text_secondary": "#b0b0b0",
                "error": "#f44336",
                "warning": "#ff9800",
                "success": "#4caf50",
                "info": "#2196f3"
            },
            "light": {
                "primary": "#1976d2",
                "secondary": "#1565c0",
                "accent": "#388e3c",
                "background": "#fafafa",
                "surface": "#ffffff",
                "text": "#212121",
                "text_secondary": "#757575",
                "error": "#d32f2f",
                "warning": "#f57c00",
                "success": "#388e3c",
                "info": "#1976d2"
            }
        }

    def set_theme(self, theme: str = "dark", color: str = "blue"):
        """Set the application theme."""
        self.current_theme = theme
        self.current_color = color

        # Apply to customtkinter with error handling
        try:
            ctk.set_appearance_mode(theme)
            ctk.set_default_color_theme(color)
        except Exception as e:
            # Ignore theme setting errors to prevent application crashes
            print(f"Warning: Theme setting failed: {e}")
            pass

    def get_color(self, color_name: str) -> str:
        """Get a color from the current theme."""
        return self.colors[self.current_theme].get(color_name, "#000000")

    def get_font(self, size: int = 12, weight: str = "normal") -> Tuple[str, int, str]:
        """Get a font tuple for tkinter widgets."""
        font_family = "Segoe UI" if os.name == 'nt' else "San Francisco" if sys.platform == 'darwin' else "Ubuntu"
        return (font_family, size, weight)

    def get_button_colors(self, style: str = "primary") -> Dict[str, str]:
        """Get colors for button styling."""
        if style == "primary":
            return {
                "fg_color": self.get_color("primary"),
                "hover_color": self.get_color("secondary"),
                "text_color": "#ffffff"
            }
        elif style == "secondary":
            return {
                "fg_color": "transparent",
                "hover_color": self.get_color("surface"),
                "text_color": self.get_color("text"),
                "border_width": 2,
                "border_color": self.get_color("primary")
            }
        elif style == "success":
            return {
                "fg_color": self.get_color("success"),
                "hover_color": "#2e7d32",
                "text_color": "#ffffff"
            }
        elif style == "warning":
            return {
                "fg_color": self.get_color("warning"),
                "hover_color": "#e65100",
                "text_color": "#ffffff"
            }
        elif style == "error":
            return {
                "fg_color": self.get_color("error"),
                "hover_color": "#c62828",
                "text_color": "#ffffff"
            }
        return {}

    def get_frame_colors(self, elevated: bool = False) -> Dict[str, str]:
        """Get colors for frame styling."""
        if elevated:
            return {
                "fg_color": self.get_color("surface"),
                "corner_radius": 10,
                "border_width": 1,
                "border_color": self.get_color("primary")
            }
        return {
            "fg_color": self.get_color("surface"),
            "corner_radius": 8
        }

    def get_entry_colors(self) -> Dict[str, str]:
        """Get colors for entry widget styling."""
        return {
            "fg_color": self.get_color("surface"),
            "border_color": self.get_color("primary"),
            "text_color": self.get_color("text"),
            "placeholder_text_color": self.get_color("text_secondary")
        }

    def get_label_colors(self, style: str = "normal") -> Dict[str, str]:
        """Get colors for label styling."""
        colors = {
            "text_color": self.get_color("text")
        }

        if style == "heading":
            colors["font"] = self.get_font(16, "bold")
        elif style == "subheading":
            colors["font"] = self.get_font(14, "bold")
        elif style == "caption":
            colors["text_color"] = self.get_color("text_secondary")
            colors["font"] = self.get_font(10)

        return colors

    def create_styled_frame(self, parent, elevated: bool = False, **kwargs) -> ctk.CTkFrame:
        """Create a styled frame widget."""
        colors = self.get_frame_colors(elevated)
        colors.update(kwargs)
        return ctk.CTkFrame(parent, **colors)

    def create_styled_button(self, parent, style: str = "primary", **kwargs) -> ctk.CTkButton:
        """Create a styled button widget."""
        colors = self.get_button_colors(style)
        colors.update(kwargs)
        return ctk.CTkButton(parent, **colors)

    def create_styled_entry(self, parent, **kwargs) -> ctk.CTkEntry:
        """Create a styled entry widget."""
        colors = self.get_entry_colors()
        colors.update(kwargs)
        return ctk.CTkEntry(parent, **colors)

    def create_styled_label(self, parent, style: str = "normal", **kwargs) -> ctk.CTkLabel:
        """Create a styled label widget."""
        colors = self.get_label_colors(style)
        colors.update(kwargs)
        return ctk.CTkLabel(parent, **colors)