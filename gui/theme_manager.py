"""Theme and styling management for the GUI."""

import os
import sys
import customtkinter as ctk
from typing import Dict, Tuple, Optional

class ThemeManager:
    """Manages application themes and styling."""

    # Font size constants - improved for better readability
    FONT_SIZE_DISPLAY = 36      # Large icons, special elements
    FONT_SIZE_TITLE_LARGE = 26  # Main page titles
    FONT_SIZE_TITLE = 22        # Section titles
    FONT_SIZE_HEADING_LARGE = 20  # Large headings
    FONT_SIZE_HEADING = 18      # Standard headings
    FONT_SIZE_SUBHEADING = 15   # Subheadings
    FONT_SIZE_BODY_LARGE = 14   # Emphasized body text
    FONT_SIZE_BODY = 13         # Primary body text (default)
    FONT_SIZE_BODY_SMALL = 12   # Secondary body text
    FONT_SIZE_CAPTION = 11      # Captions and hints
    FONT_SIZE_MONOSPACE = 12    # Code and technical text

    def __init__(self):
        self.current_theme = "dark"
        self.current_color = "blue"
        self._setup_colors()
        self._setup_font_families()

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

    def _setup_font_families(self):
        """Setup font families for different platforms."""
        # Sans-serif font for UI elements
        if os.name == 'nt':  # Windows
            self.font_family = "Segoe UI"
            self.monospace_family = "Consolas"
        elif sys.platform == 'darwin':  # macOS
            self.font_family = "SF Pro Display"
            self.monospace_family = "SF Mono"
        else:  # Linux
            self.font_family = "Ubuntu"
            self.monospace_family = "Ubuntu Mono"

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

    # ========================================================================
    # Font Methods - Comprehensive font system for improved readability
    # ========================================================================

    def get_font(self, size: Optional[int] = None, weight: str = "normal",
                 slant: str = "roman", family: Optional[str] = None) -> ctk.CTkFont:
        """
        Get a CTkFont object with specified properties.

        Args:
            size: Font size in pixels (default: FONT_SIZE_BODY = 13)
            weight: "normal" or "bold"
            slant: "roman" or "italic"
            family: Optional font family (default: platform-specific sans-serif)

        Returns:
            CTkFont object
        """
        if size is None:
            size = self.FONT_SIZE_BODY
        if family is None:
            family = self.font_family

        return ctk.CTkFont(family=family, size=size, weight=weight, slant=slant)

    # Display and Title Fonts
    def get_display_font(self, weight: str = "normal") -> ctk.CTkFont:
        """Large display font for icons and special elements (36px)."""
        return self.get_font(size=self.FONT_SIZE_DISPLAY, weight=weight)

    def get_title_large_font(self, weight: str = "bold") -> ctk.CTkFont:
        """Large title font for main page titles (26px)."""
        return self.get_font(size=self.FONT_SIZE_TITLE_LARGE, weight=weight)

    def get_title_font(self, weight: str = "bold") -> ctk.CTkFont:
        """Title font for section titles (22px)."""
        return self.get_font(size=self.FONT_SIZE_TITLE, weight=weight)

    # Heading Fonts
    def get_heading_large_font(self, weight: str = "bold") -> ctk.CTkFont:
        """Large heading font (20px)."""
        return self.get_font(size=self.FONT_SIZE_HEADING_LARGE, weight=weight)

    def get_heading_font(self, weight: str = "bold") -> ctk.CTkFont:
        """Standard heading font (18px)."""
        return self.get_font(size=self.FONT_SIZE_HEADING, weight=weight)

    def get_subheading_font(self, weight: str = "bold") -> ctk.CTkFont:
        """Subheading font (15px)."""
        return self.get_font(size=self.FONT_SIZE_SUBHEADING, weight=weight)

    # Body Fonts
    def get_body_large_font(self, weight: str = "normal") -> ctk.CTkFont:
        """Large body text font for emphasis (14px)."""
        return self.get_font(size=self.FONT_SIZE_BODY_LARGE, weight=weight)

    def get_body_font(self, weight: str = "normal") -> ctk.CTkFont:
        """Standard body text font - primary text size (13px)."""
        return self.get_font(size=self.FONT_SIZE_BODY, weight=weight)

    def get_body_small_font(self, weight: str = "normal") -> ctk.CTkFont:
        """Small body text font for secondary information (12px)."""
        return self.get_font(size=self.FONT_SIZE_BODY_SMALL, weight=weight)

    def get_caption_font(self, weight: str = "normal", slant: str = "roman") -> ctk.CTkFont:
        """Caption font for hints and annotations (11px)."""
        return self.get_font(size=self.FONT_SIZE_CAPTION, weight=weight, slant=slant)

    # Monospace Fonts
    def get_monospace_font(self, size: Optional[int] = None, weight: str = "normal") -> ctk.CTkFont:
        """
        Monospace font for code, technical data, and fixed-width text.

        Args:
            size: Font size (default: FONT_SIZE_MONOSPACE = 12)
            weight: "normal" or "bold"
        """
        if size is None:
            size = self.FONT_SIZE_MONOSPACE
        return ctk.CTkFont(family=self.monospace_family, size=size, weight=weight)

    # Legacy compatibility method (returns tuple for old code)
    def get_font_tuple(self, size: int = 12, weight: str = "normal") -> Tuple[str, int, str]:
        """
        Get a font tuple for legacy tkinter widgets.
        DEPRECATED: Use get_font() or specific font methods instead.
        """
        return (self.font_family, size, weight)

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
        """Get colors for label styling with improved font system."""
        colors = {
            "text_color": self.get_color("text")
        }

        if style == "heading":
            colors["font"] = self.get_heading_font()
        elif style == "subheading":
            colors["font"] = self.get_subheading_font()
        elif style == "caption":
            colors["text_color"] = self.get_color("text_secondary")
            colors["font"] = self.get_caption_font()

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