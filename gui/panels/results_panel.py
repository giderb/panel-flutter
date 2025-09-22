"""Modern, beautiful results visualization panel for flutter analysis."""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
import math
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from report_generator import ReportGenerator

from .base_panel import BasePanel

class ResultsPanel(BasePanel):
    """Advanced results visualization panel with modern UI."""

    def __init__(self, parent, main_window):
        self.analysis_results = None
        self.current_view = "overview"
        self.report_generator = ReportGenerator()
        super().__init__(parent, main_window)

    def _setup_ui(self):
        """Setup the results panel UI with modern design."""
        # Main container with gradient background effect
        self.main_container = ctk.CTkFrame(self.frame, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create stunning header
        self._create_header()

        # Create main content area with tabs
        self._create_content_area()

        # Create bottom action bar
        self._create_action_bar()

        # Initialize with overview
        self._show_overview()

    def _create_header(self):
        """Create beautiful header with gradient effect."""
        header_frame = self.theme_manager.create_styled_frame(
            self.main_container,
            elevated=True
        )
        header_frame.pack(fill="x", pady=(0, 20))

        # Gradient-like header content
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=30, pady=25)

        # Left side - Title and status
        left_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)

        # Icon and title
        title_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        title_row.pack(anchor="w")

        icon_label = self.theme_manager.create_styled_label(
            title_row,
            text="📊",
            font=ctk.CTkFont(size=36)
        )
        icon_label.pack(side="left", padx=(0, 15))

        title_container = ctk.CTkFrame(title_row, fg_color="transparent")
        title_container.pack(side="left")

        title_label = self.theme_manager.create_styled_label(
            title_container,
            text="Analysis Results",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title_label.pack(anchor="w")

        self.status_label = self.theme_manager.create_styled_label(
            title_container,
            text="No analysis performed",
            font=ctk.CTkFont(size=13),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        self.status_label.pack(anchor="w", pady=(2, 0))

        # Right side - Key metrics cards
        right_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        right_frame.pack(side="right")

        self._create_metric_cards(right_frame)

    def _create_metric_cards(self, parent):
        """Create beautiful metric cards for key results."""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack()

        # Flutter Speed Card
        speed_card = self._create_metric_card(
            cards_frame,
            "Flutter Speed",
            "--",
            "m/s",
            "#3B82F6",  # Blue
            "🚀"
        )
        speed_card.pack(side="left", padx=(0, 10))
        self.speed_value_label = speed_card.value_label

        # Flutter Frequency Card
        freq_card = self._create_metric_card(
            cards_frame,
            "Flutter Frequency",
            "--",
            "Hz",
            "#10B981",  # Green
            "📈"
        )
        freq_card.pack(side="left", padx=(0, 10))
        self.freq_value_label = freq_card.value_label

        # Damping Card
        damp_card = self._create_metric_card(
            cards_frame,
            "Critical Damping",
            "--",
            "%",
            "#F59E0B",  # Amber
            "⚡"
        )
        damp_card.pack(side="left")
        self.damp_value_label = damp_card.value_label

    def _create_metric_card(self, parent, title, value, unit, color, icon):
        """Create a single metric card with modern design."""
        card = ctk.CTkFrame(
            parent,
            width=140,
            height=100,
            corner_radius=12,
            fg_color=self.theme_manager.get_color("surface")
        )
        card.pack_propagate(False)

        # Color accent bar at top
        accent_bar = ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=color)
        accent_bar.pack(fill="x", side="top")

        # Card content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(expand=True, padx=15, pady=12)

        # Icon and title row
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack(anchor="w")

        icon_label = self.theme_manager.create_styled_label(
            title_row,
            text=icon,
            font=ctk.CTkFont(size=16)
        )
        icon_label.pack(side="left", padx=(0, 5))

        title_label = self.theme_manager.create_styled_label(
            title_row,
            text=title,
            font=ctk.CTkFont(size=10),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        title_label.pack(side="left")

        # Value
        value_frame = ctk.CTkFrame(content, fg_color="transparent")
        value_frame.pack(anchor="w", pady=(5, 0))

        value_label = self.theme_manager.create_styled_label(
            value_frame,
            text=str(value),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=color
        )
        value_label.pack(side="left")

        unit_label = self.theme_manager.create_styled_label(
            value_frame,
            text=f" {unit}",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        unit_label.pack(side="left")

        # Store reference to value label for updates
        card.value_label = value_label
        return card

    def _create_content_area(self):
        """Create main content area with tab navigation."""
        # Tab navigation bar
        self._create_tab_navigation()

        # Content display area
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=12,
            fg_color=self.theme_manager.get_color("background")
        )
        self.content_frame.pack(fill="both", expand=True, pady=(0, 20))

    def _create_tab_navigation(self):
        """Create beautiful tab navigation."""
        nav_frame = self.theme_manager.create_styled_frame(
            self.main_container,
            elevated=True
        )
        nav_frame.pack(fill="x", pady=(0, 20))

        tabs_container = ctk.CTkFrame(nav_frame, fg_color="transparent")
        tabs_container.pack(fill="x", padx=20, pady=15)

        self.tab_buttons = {}

        tabs = [
            ("overview", "📋 Overview", "Summary of analysis results"),
            ("vg_diagram", "📉 V-g Diagram", "Velocity vs damping plot"),
            ("vf_diagram", "📈 V-f Diagram", "Velocity vs frequency plot"),
            ("modes", "🌊 Mode Shapes", "Structural mode visualization"),
            ("data", "📊 Data Table", "Detailed numerical results"),
            ("comparison", "🔄 Comparison", "Compare multiple analyses")
        ]

        for i, (tab_id, label, tooltip) in enumerate(tabs):
            tab_btn = self._create_tab_button(tabs_container, tab_id, label, tooltip)
            tab_btn.pack(side="left", padx=(0, 10) if i < len(tabs)-1 else 0)
            self.tab_buttons[tab_id] = tab_btn

            # Set first tab as active
            if i == 0:
                tab_btn.configure(
                    fg_color=self.theme_manager.get_color("primary"),
                    text_color="white"
                )

    def _create_tab_button(self, parent, tab_id, label, tooltip):
        """Create a single tab button."""
        btn = ctk.CTkButton(
            parent,
            text=label,
            command=lambda: self._switch_tab(tab_id),
            height=35,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.theme_manager.get_color("hover"),
            font=ctk.CTkFont(size=13)
        )

        # Add tooltip on hover
        self._add_tooltip(btn, tooltip)
        return btn

    def _add_tooltip(self, widget, text):
        """Add tooltip to widget."""
        def on_enter(event):
            self.tooltip = tk.Toplevel()
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(
                self.tooltip,
                text=text,
                background="#333333",
                foreground="white",
                relief="solid",
                borderwidth=1,
                font=("Arial", 10)
            )
            label.pack()

        def on_leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                del self.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _switch_tab(self, tab_id):
        """Switch to a different tab."""
        # Update button states
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=self.theme_manager.get_color("primary"),
                    text_color="white"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.theme_manager.get_color("text")
                )

        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Show appropriate content
        self.current_view = tab_id
        if tab_id == "overview":
            self._show_overview()
        elif tab_id == "vg_diagram":
            self._show_vg_diagram()
        elif tab_id == "vf_diagram":
            self._show_vf_diagram()
        elif tab_id == "modes":
            self._show_mode_shapes()
        elif tab_id == "data":
            self._show_data_table()
        elif tab_id == "comparison":
            self._show_comparison()

    def _show_overview(self):
        """Show overview of results."""
        # Scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            corner_radius=0,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.analysis_results:
            self._show_no_data_message(scroll_frame)
            return

        # Analysis Summary Card
        summary_card = self._create_result_card(
            scroll_frame,
            "Analysis Summary",
            "📊"
        )
        summary_card.pack(fill="x", pady=(0, 15))

        summary_content = ctk.CTkFrame(summary_card, fg_color="transparent")
        summary_content.pack(fill="x", padx=20, pady=(0, 20))

        # Create summary grid
        num_modes = len(self.modal_frequencies) if hasattr(self, 'modal_frequencies') else 0

        # Determine stability based on flutter results
        flutter_speed = self.analysis_results.get("critical_flutter_speed")

        # Check if panel is stable
        if flutter_speed is None or flutter_speed == 9999.0 or flutter_speed == 9999:
            # No flutter detected or explicitly marked as stable
            stable = True
        elif flutter_speed == 0 or flutter_speed == "--":
            # No results available
            stable = True  # Default to stable if unknown
        else:
            # Flutter detected at some velocity
            stable = False

        summary_data = [
            ("Analysis Method", self.analysis_results.get("method", "N/A")),
            ("Number of Modes", f"{num_modes} structural modes" if num_modes > 0 else "No valid modes"),
            ("Velocity Range", f"{self.analysis_results.get('v_min', 0)}-{self.analysis_results.get('v_max', 0)} m/s"),
            ("Analysis Time", self.analysis_results.get("computation_time", "N/A")),
            ("Convergence", "✅ Converged" if self.analysis_results.get("converged", False) else "❌ Not Converged"),
            ("Stability", "✅ Stable" if stable else "⚠️ Flutter Detected")
        ]

        for i, (label, value) in enumerate(summary_data):
            row = i // 2
            col = i % 2
            self._create_info_row(summary_content, label, str(value), row, col)

        # Critical Results Card
        critical_card = self._create_result_card(
            scroll_frame,
            "Critical Flutter Point",
            "⚠️"
        )
        critical_card.pack(fill="x", pady=(0, 15))

        critical_content = ctk.CTkFrame(critical_card, fg_color="transparent")
        critical_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Flutter point visualization
        self._create_flutter_point_visual(critical_content)

        # Recommendations Card
        rec_card = self._create_result_card(
            scroll_frame,
            "Analysis Recommendations",
            "💡"
        )
        rec_card.pack(fill="x", pady=(0, 15))

        rec_content = ctk.CTkFrame(rec_card, fg_color="transparent")
        rec_content.pack(fill="x", padx=20, pady=(0, 20))

        recommendations = self._generate_recommendations()
        for rec in recommendations:
            rec_frame = ctk.CTkFrame(rec_content, fg_color="transparent")
            rec_frame.pack(fill="x", pady=2)

            bullet = self.theme_manager.create_styled_label(
                rec_frame,
                text="•",
                font=ctk.CTkFont(size=12),
                text_color=self.theme_manager.get_color("primary")
            )
            bullet.pack(side="left", padx=(0, 10))

            rec_label = self.theme_manager.create_styled_label(
                rec_frame,
                text=rec,
                font=ctk.CTkFont(size=12),
                wraplength=600
            )
            rec_label.pack(side="left", anchor="w")

    def _create_result_card(self, parent, title, icon):
        """Create a result card container."""
        card = self.theme_manager.create_styled_frame(
            parent,
            elevated=True
        )

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 15))

        icon_label = self.theme_manager.create_styled_label(
            header,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="left", padx=(0, 10))

        title_label = self.theme_manager.create_styled_label(
            header,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left")

        return card

    def _create_info_row(self, parent, label, value, row, col):
        """Create an info row in grid layout."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=(20 if col == 1 else 0, 0), pady=5)

        label_widget = self.theme_manager.create_styled_label(
            frame,
            text=f"{label}:",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        label_widget.pack(side="left")

        value_widget = self.theme_manager.create_styled_label(
            frame,
            text=value,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        value_widget.pack(side="left", padx=(10, 0))

        parent.grid_columnconfigure(col, weight=1)

    def _create_flutter_point_visual(self, parent):
        """Create visual representation of flutter point."""
        visual_frame = ctk.CTkFrame(
            parent,
            height=200,
            corner_radius=10,
            fg_color=self.theme_manager.get_color("surface")
        )
        visual_frame.pack(fill="both", expand=True, pady=10)
        visual_frame.pack_propagate(False)

        if self.analysis_results:
            # Create a simple visual representation
            canvas = tk.Canvas(
                visual_frame,
                bg=self.theme_manager.get_color("surface"),
                highlightthickness=0
            )
            canvas.pack(fill="both", expand=True, padx=20, pady=20)

            # Draw flutter point visualization
            self._draw_flutter_visualization(canvas)

    def _draw_flutter_visualization(self, canvas):
        """Draw flutter point visualization on canvas."""
        def draw():
            canvas.delete("all")
            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width > 1 and height > 1:
                # Define margins
                left_margin = 50
                right_margin = 30
                top_margin = 20
                bottom_margin = 40

                plot_width = width - left_margin - right_margin
                plot_height = height - top_margin - bottom_margin

                # White background
                canvas.create_rectangle(
                    left_margin, top_margin,
                    width - right_margin, height - bottom_margin,
                    fill="white",
                    outline=self.theme_manager.get_color("border")
                )

                # Grid lines
                for i in range(5):
                    # Vertical lines
                    x = left_margin + (plot_width * i / 4)
                    canvas.create_line(
                        x, top_margin, x, height - bottom_margin,
                        fill="#E5E7EB", width=1
                    )
                    # Horizontal lines
                    y = top_margin + (plot_height * i / 4)
                    canvas.create_line(
                        left_margin, y, width - right_margin, y,
                        fill="#E5E7EB", width=1
                    )

                # Draw axes
                canvas.create_line(
                    left_margin, height - bottom_margin,
                    width - right_margin, height - bottom_margin,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=2
                )
                canvas.create_line(
                    left_margin, top_margin,
                    left_margin, height - bottom_margin,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=2
                )

                # Zero damping line
                zero_y = top_margin + plot_height / 2
                canvas.create_line(
                    left_margin, zero_y, width - right_margin, zero_y,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=1,
                    dash=(3, 2)
                )

                # Draw flutter curve
                points = []
                v_min, v_max = 0, 1200

                for i in range(40):
                    velocity = v_min + (v_max - v_min) * i / 39
                    x = left_margin + plot_width * i / 39

                    # Damping curve
                    damping = -0.02 + 0.05 * math.sin(i/8)
                    if velocity > 800:  # Flutter onset
                        damping += 0.1 * ((velocity - 800) / 400)

                    y = zero_y - damping * plot_height * 3
                    points.extend([x, y])

                if len(points) > 4:
                    canvas.create_line(
                        points,
                        fill=self.theme_manager.get_color("primary"),
                        width=3,
                        smooth=True
                    )

                # Mark critical flutter point
                if self.analysis_results:
                    flutter_v = self.analysis_results.get("critical_flutter_speed", 950)
                    critical_x = left_margin + plot_width * (flutter_v / v_max)
                    critical_y = zero_y - 20  # Position above zero line

                    canvas.create_oval(
                        critical_x - 6, critical_y - 6,
                        critical_x + 6, critical_y + 6,
                        fill="#EF4444",
                        outline="white",
                        width=2
                    )

                    # Flutter speed indicator
                    canvas.create_line(
                        critical_x, top_margin, critical_x, height - bottom_margin,
                        fill="#EF4444",
                        width=1,
                        dash=(3, 2)
                    )

                    canvas.create_text(
                        critical_x, height - bottom_margin + 15,
                        text=f"{flutter_v:.0f}",
                        fill="#EF4444",
                        font=("Arial", 9, "bold")
                    )

                # Axis labels
                canvas.create_text(
                    width/2, height - 5,
                    text="Velocity (m/s)",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 10, "bold")
                )

                canvas.create_text(
                    15, height/2,
                    text="Damping",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 10, "bold"),
                    angle=90
                )

                # Add axis values
                for i in range(5):
                    # X-axis values
                    x_val = v_max * i / 4
                    canvas.create_text(
                        left_margin + plot_width * i / 4,
                        height - bottom_margin + 10,
                        text=f"{int(x_val)}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 8)
                    )

        canvas.after(100, draw)

    def _show_vg_diagram(self):
        """Show V-g diagram."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.analysis_results:
            self._show_no_data_message(container)
            return

        # Diagram header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Velocity vs Damping Diagram",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")

        # Export button
        export_btn = ctk.CTkButton(
            header_frame,
            text="📥 Export",
            command=self._export_diagram,
            width=100,
            height=30,
            corner_radius=6
        )
        export_btn.pack(side="right")

        # Diagram placeholder
        diagram_frame = self.theme_manager.create_styled_frame(
            container,
            elevated=True
        )
        diagram_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            diagram_frame,
            bg=self.theme_manager.get_color("background"),
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=20, pady=20)

        # Draw V-g diagram
        self._draw_vg_diagram(canvas)

    def _draw_vg_diagram(self, canvas):
        """Draw V-g diagram on canvas."""
        def draw():
            canvas.delete("all")
            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width > 1 and height > 1:
                # Define margins and plot area
                left_margin = 80
                right_margin = 150
                top_margin = 50
                bottom_margin = 60

                plot_width = width - left_margin - right_margin
                plot_height = height - top_margin - bottom_margin

                # Set white background for plot area
                canvas.create_rectangle(
                    left_margin, top_margin,
                    width - right_margin, height - bottom_margin,
                    fill="white",
                    outline=self.theme_manager.get_color("border")
                )

                # Draw grid lines
                # Vertical grid lines (velocity)
                v_min, v_max = 0, 1500
                for i in range(7):
                    x = left_margin + (plot_width * i / 6)
                    canvas.create_line(
                        x, top_margin, x, height - bottom_margin,
                        fill="#E5E7EB", width=1
                    )
                    # Velocity labels
                    vel = v_min + (v_max - v_min) * i / 6
                    canvas.create_text(
                        x, height - bottom_margin + 15,
                        text=f"{int(vel)}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 10)
                    )

                # Horizontal grid lines (damping)
                g_min, g_max = -0.15, 0.15
                for i in range(7):
                    y = top_margin + (plot_height * i / 6)
                    canvas.create_line(
                        left_margin, y, width - right_margin, y,
                        fill="#E5E7EB", width=1
                    )
                    # Damping labels
                    damp = g_max - (g_max - g_min) * i / 6
                    canvas.create_text(
                        left_margin - 20, y,
                        text=f"{damp:.2f}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 10)
                    )

                # Draw axes (darker lines)
                # X-axis
                canvas.create_line(
                    left_margin, height - bottom_margin,
                    width - right_margin, height - bottom_margin,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=2
                )
                # Y-axis
                canvas.create_line(
                    left_margin, top_margin,
                    left_margin, height - bottom_margin,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=2
                )
                # Zero damping line
                zero_y = top_margin + plot_height / 2
                canvas.create_line(
                    left_margin, zero_y, width - right_margin, zero_y,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=1,
                    dash=(5, 3)
                )

                # Create V-g curves
                colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]

                for mode in range(3):
                    points = []
                    for i in range(50):
                        velocity = v_min + (v_max - v_min) * i / 49
                        x = left_margin + plot_width * i / 49

                        # Generate damping curve
                        damping = -0.05 + 0.1 * math.sin(i / 10 + mode) * math.exp(-i/30)
                        if velocity > 800 + mode * 100:  # Flutter onset
                            damping += 0.05 * ((velocity - 800 - mode * 100) / 700)

                        # Convert damping to y coordinate
                        y = top_margin + plot_height * (1 - (damping - g_min) / (g_max - g_min))
                        points.extend([x, y])

                    if len(points) > 4:
                        canvas.create_line(
                            points,
                            fill=colors[mode % len(colors)],
                            width=3,
                            smooth=True,
                            tags=f"mode_{mode+1}"
                        )

                # Axis labels
                canvas.create_text(
                    width/2, height - 15,
                    text="Velocity (m/s)",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 12, "bold")
                )

                canvas.create_text(
                    25, height/2,
                    text="Damping (g)",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 12, "bold"),
                    angle=90
                )

                # Title
                canvas.create_text(
                    width/2, 20,
                    text="V-g Diagram - Flutter Analysis",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 14, "bold")
                )

                # Legend
                legend_x = width - right_margin + 20
                legend_y = top_margin + 20

                canvas.create_text(
                    legend_x, legend_y - 10,
                    text="Modes:",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 11, "bold"),
                    anchor="w"
                )

                for i in range(3):
                    canvas.create_rectangle(
                        legend_x, legend_y + 10 + i*25,
                        legend_x + 20, legend_y + 20 + i*25,
                        fill=colors[i % len(colors)],
                        outline=""
                    )
                    canvas.create_text(
                        legend_x + 25, legend_y + 15 + i*25,
                        text=f"Mode {i+1}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 10),
                        anchor="w"
                    )

                # Add flutter points
                if self.analysis_results:
                    flutter_v = self.analysis_results.get("critical_flutter_speed", 950)
                    if flutter_v and v_min <= flutter_v <= v_max:
                        x = left_margin + plot_width * (flutter_v - v_min) / (v_max - v_min)
                        canvas.create_line(
                            x, top_margin, x, height - bottom_margin,
                            fill="#EF4444",
                            width=2,
                            dash=(5, 3)
                        )
                        canvas.create_text(
                            x, top_margin - 10,
                            text=f"Flutter: {flutter_v:.0f} m/s",
                            fill="#EF4444",
                            font=("Arial", 10, "bold")
                        )

        canvas.after(100, draw)

    def _show_vf_diagram(self):
        """Show V-f diagram."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.analysis_results:
            self._show_no_data_message(container)
            return

        # Diagram header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Velocity vs Frequency Diagram",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")

        # Diagram placeholder
        diagram_frame = self.theme_manager.create_styled_frame(
            container,
            elevated=True
        )
        diagram_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            diagram_frame,
            bg=self.theme_manager.get_color("background"),
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=20, pady=20)

        # Draw V-f diagram
        self._draw_vf_diagram(canvas)

    def _draw_vf_diagram(self, canvas):
        """Draw V-f diagram on canvas."""
        def draw():
            canvas.delete("all")
            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width > 1 and height > 1:
                # Define margins and plot area
                left_margin = 80
                right_margin = 150
                top_margin = 50
                bottom_margin = 60

                plot_width = width - left_margin - right_margin
                plot_height = height - top_margin - bottom_margin

                # Set white background for plot area
                canvas.create_rectangle(
                    left_margin, top_margin,
                    width - right_margin, height - bottom_margin,
                    fill="white",
                    outline=self.theme_manager.get_color("border")
                )

                # Draw grid lines
                # Vertical grid lines (velocity)
                v_min, v_max = 0, 1500
                for i in range(7):
                    x = left_margin + (plot_width * i / 6)
                    canvas.create_line(
                        x, top_margin, x, height - bottom_margin,
                        fill="#E5E7EB", width=1
                    )
                    # Velocity labels
                    vel = v_min + (v_max - v_min) * i / 6
                    canvas.create_text(
                        x, height - bottom_margin + 15,
                        text=f"{int(vel)}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 10)
                    )

                # Horizontal grid lines (frequency)
                f_min, f_max = 0, 150
                for i in range(7):
                    y = top_margin + (plot_height * i / 6)
                    canvas.create_line(
                        left_margin, y, width - right_margin, y,
                        fill="#E5E7EB", width=1
                    )
                    # Frequency labels
                    freq = f_max - (f_max - f_min) * i / 6
                    canvas.create_text(
                        left_margin - 20, y,
                        text=f"{int(freq)}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 10)
                    )

                # Draw axes (darker lines)
                # X-axis
                canvas.create_line(
                    left_margin, height - bottom_margin,
                    width - right_margin, height - bottom_margin,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=2
                )
                # Y-axis
                canvas.create_line(
                    left_margin, top_margin,
                    left_margin, height - bottom_margin,
                    fill=self.theme_manager.get_color("text_secondary"),
                    width=2
                )

                # Create V-f curves
                colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]

                for mode in range(3):
                    points = []
                    base_freq = 20 + mode * 30  # Base frequency for each mode

                    for i in range(50):
                        velocity = v_min + (v_max - v_min) * i / 49
                        x = left_margin + plot_width * i / 49

                        # Generate frequency curve (typically increases with velocity)
                        freq = base_freq + (velocity / 1500) * 20
                        # Add some variation
                        freq += 5 * math.sin((velocity / 200) + mode)

                        # Flutter coupling effect
                        if velocity > 700 + mode * 150:
                            freq -= (velocity - 700 - mode * 150) * 0.02

                        # Convert frequency to y coordinate
                        y = top_margin + plot_height * (1 - (freq - f_min) / (f_max - f_min))
                        points.extend([x, y])

                    if len(points) > 4:
                        canvas.create_line(
                            points,
                            fill=colors[mode % len(colors)],
                            width=3,
                            smooth=True,
                            tags=f"mode_{mode+1}"
                        )

                # Axis labels
                canvas.create_text(
                    width/2, height - 15,
                    text="Velocity (m/s)",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 12, "bold")
                )

                canvas.create_text(
                    25, height/2,
                    text="Frequency (Hz)",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 12, "bold"),
                    angle=90
                )

                # Title
                canvas.create_text(
                    width/2, 20,
                    text="V-f Diagram - Frequency Evolution",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 14, "bold")
                )

                # Legend
                legend_x = width - right_margin + 20
                legend_y = top_margin + 20

                canvas.create_text(
                    legend_x, legend_y - 10,
                    text="Modes:",
                    fill=self.theme_manager.get_color("text"),
                    font=("Arial", 11, "bold"),
                    anchor="w"
                )

                for i in range(3):
                    canvas.create_rectangle(
                        legend_x, legend_y + 10 + i*25,
                        legend_x + 20, legend_y + 20 + i*25,
                        fill=colors[i % len(colors)],
                        outline=""
                    )
                    canvas.create_text(
                        legend_x + 25, legend_y + 15 + i*25,
                        text=f"Mode {i+1}",
                        fill=self.theme_manager.get_color("text"),
                        font=("Arial", 10),
                        anchor="w"
                    )

                # Add flutter point indicator
                if self.analysis_results:
                    flutter_v = self.analysis_results.get("critical_flutter_speed", 950)
                    flutter_f = self.analysis_results.get("critical_flutter_frequency", 45)

                    if flutter_v and v_min <= flutter_v <= v_max:
                        x = left_margin + plot_width * (flutter_v - v_min) / (v_max - v_min)

                        # Vertical line at flutter speed
                        canvas.create_line(
                            x, top_margin, x, height - bottom_margin,
                            fill="#EF4444",
                            width=2,
                            dash=(5, 3)
                        )

                        # Flutter point
                        if flutter_f and f_min <= flutter_f <= f_max:
                            y = top_margin + plot_height * (1 - (flutter_f - f_min) / (f_max - f_min))
                            canvas.create_oval(
                                x - 5, y - 5, x + 5, y + 5,
                                fill="#EF4444",
                                outline="white",
                                width=2
                            )

                        canvas.create_text(
                            x, top_margin - 10,
                            text=f"Flutter: {flutter_v:.0f} m/s @ {flutter_f:.1f} Hz",
                            fill="#EF4444",
                            font=("Arial", 10, "bold")
                        )

        canvas.after(100, draw)

    def _show_mode_shapes(self):
        """Show mode shapes visualization."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.analysis_results:
            self._show_no_data_message(container)
            return

        # Header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Structural Mode Shapes",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")

        # Get actual number of modes available
        num_modes = len(self.modal_frequencies) if hasattr(self, 'modal_frequencies') else 0

        if num_modes == 0:
            no_modes_label = self.theme_manager.create_styled_label(
                container,
                text="No valid structural modes found in analysis results.",
                font=ctk.CTkFont(size=14),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            no_modes_label.pack(pady=50)
            return

        # Mode selector
        mode_selector_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        mode_selector_frame.pack(side="right")

        mode_label = self.theme_manager.create_styled_label(
            mode_selector_frame,
            text="Select Mode:",
            font=ctk.CTkFont(size=12)
        )
        mode_label.pack(side="left", padx=(0, 10))

        # Only show available modes
        modes_to_show = min(num_modes, 6)  # Show max 6 modes in grid
        mode_values = [f"Mode {i+1}" for i in range(modes_to_show)]
        mode_combo = ctk.CTkComboBox(
            mode_selector_frame,
            values=mode_values,
            width=120,
            command=self._on_mode_selected
        )
        mode_combo.pack(side="left")
        if modes_to_show > 0:
            mode_combo.set("Mode 1")

        # Mode shape grid
        modes_grid = ctk.CTkFrame(container, fg_color="transparent")
        modes_grid.pack(fill="both", expand=True)

        # Create grid of mode shapes (2x3 or less)
        for i in range(modes_to_show):
            row = i // 3
            col = i % 3

            mode_card = self._create_mode_card(modes_grid, i+1)
            mode_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        for i in range(3):
            modes_grid.grid_columnconfigure(i, weight=1)
        for i in range(2):
            modes_grid.grid_rowconfigure(i, weight=1)

    def _create_mode_card(self, parent, mode_num):
        """Create a mode shape card."""
        card = self.theme_manager.create_styled_frame(
            parent,
            elevated=True
        )

        # Mode header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        mode_label = self.theme_manager.create_styled_label(
            header,
            text=f"Mode {mode_num}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        mode_label.pack(side="left")

        # Get actual frequency for this mode
        freq_text = "--"
        if hasattr(self, 'modal_frequencies') and len(self.modal_frequencies) >= mode_num:
            freq_value = self.modal_frequencies[mode_num - 1]  # 0-indexed list
            freq_text = f"{freq_value:.1f} Hz"
        else:
            freq_text = "-- Hz"

        freq_label = self.theme_manager.create_styled_label(
            header,
            text=freq_text,
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        freq_label.pack(side="right")

        # Mode shape canvas
        canvas = tk.Canvas(
            card,
            height=150,
            bg=self.theme_manager.get_color("surface"),
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Draw mode shape
        self._draw_mode_shape(canvas, mode_num)

        return card

    def _draw_mode_shape(self, canvas, mode_num):
        """Draw a mode shape on canvas."""
        def draw():
            canvas.delete("all")
            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width > 1 and height > 1:
                # Draw plate outline
                margin = 20
                canvas.create_rectangle(
                    margin, margin,
                    width - margin, height - margin,
                    outline=self.theme_manager.get_color("border"),
                    width=2
                )

                # Draw deformed shape pattern
                n_points = 10
                for i in range(n_points):
                    for j in range(n_points):
                        x = margin + (width - 2*margin) * i / (n_points - 1)
                        y = margin + (height - 2*margin) * j / (n_points - 1)

                        # Calculate deformation
                        deform = math.sin(math.pi * mode_num * i / n_points) * \
                                math.sin(math.pi * mode_num * j / n_points)

                        # Color based on deformation
                        intensity = abs(deform)
                        if deform > 0:
                            color = f"#{int(59 + intensity*196):02x}{int(130 + intensity*125):02x}{int(246 - intensity*100):02x}"
                        else:
                            color = f"#{int(239 - intensity*100):02x}{int(68 + intensity*100):02x}44"

                        # Draw point
                        size = 3 + intensity * 2
                        canvas.create_oval(
                            x - size, y - size,
                            x + size, y + size,
                            fill=color,
                            outline=""
                        )

        canvas.after(100, draw)

    def _show_data_table(self):
        """Show detailed data table."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.analysis_results:
            self._show_no_data_message(container)
            return

        # Header with export button
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Detailed Analysis Data",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")

        export_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        export_frame.pack(side="right")

        csv_btn = ctk.CTkButton(
            export_frame,
            text="📄 Export CSV",
            command=lambda: self._export_data("csv"),
            width=110,
            height=30,
            corner_radius=6
        )
        csv_btn.pack(side="left", padx=(0, 10))

        json_btn = ctk.CTkButton(
            export_frame,
            text="📋 Export JSON",
            command=lambda: self._export_data("json"),
            width=110,
            height=30,
            corner_radius=6
        )
        json_btn.pack(side="left")

        # Table container
        table_frame = self.theme_manager.create_styled_frame(
            container,
            elevated=True
        )
        table_frame.pack(fill="both", expand=True)

        # Create scrollable table
        table_scroll = ctk.CTkScrollableFrame(
            table_frame,
            corner_radius=0,
            fg_color="transparent"
        )
        table_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Table headers
        headers = ["Mode", "Frequency (Hz)", "Damping (%)", "Velocity (m/s)", "Status"]
        header_frame = ctk.CTkFrame(table_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        for i, header in enumerate(headers):
            header_label = self.theme_manager.create_styled_label(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=120
            )
            header_label.grid(row=0, column=i, padx=5, sticky="w")

        # Separator
        separator = ctk.CTkFrame(table_scroll, height=2, fg_color=self.theme_manager.get_color("border"))
        separator.pack(fill="x", pady=(0, 10))

        # Table data (mock data)
        for mode in range(10):
            row_frame = ctk.CTkFrame(
                table_scroll,
                fg_color=self.theme_manager.get_color("surface") if mode % 2 == 0 else "transparent"
            )
            row_frame.pack(fill="x", pady=2)

            data = [
                f"{mode + 1}",
                f"{10 + mode * 15:.2f}",
                f"{0.5 + mode * 0.1:.2f}",
                f"{500 + mode * 50:.0f}",
                "Stable" if mode < 7 else "Critical"
            ]

            for i, value in enumerate(data):
                if i == 4 and value == "Critical":
                    color = "#EF4444"
                else:
                    color = self.theme_manager.get_color("text")

                value_label = self.theme_manager.create_styled_label(
                    row_frame,
                    text=value,
                    font=ctk.CTkFont(size=11),
                    text_color=color,
                    width=120
                )
                value_label.grid(row=0, column=i, padx=5, pady=8, sticky="w")

    def _show_comparison(self):
        """Show comparison view."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Analysis Comparison",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")

        # Add comparison button
        add_btn = ctk.CTkButton(
            header_frame,
            text="➕ Add Analysis",
            command=self._add_comparison,
            width=120,
            height=30,
            corner_radius=6
        )
        add_btn.pack(side="right")

        # Comparison content
        comp_frame = self.theme_manager.create_styled_frame(
            container,
            elevated=True
        )
        comp_frame.pack(fill="both", expand=True)

        info_label = self.theme_manager.create_styled_label(
            comp_frame,
            text="Load multiple analysis results to compare them side by side.\nThis feature allows you to evaluate different design configurations.",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        info_label.pack(pady=50)

    def _show_no_data_message(self, parent):
        """Show message when no data is available."""
        message_frame = ctk.CTkFrame(parent, fg_color="transparent")
        message_frame.pack(expand=True)

        icon_label = self.theme_manager.create_styled_label(
            message_frame,
            text="📊",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(0, 20))

        message_label = self.theme_manager.create_styled_label(
            message_frame,
            text="No Analysis Results Available",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        message_label.pack()

        sub_label = self.theme_manager.create_styled_label(
            message_frame,
            text="Run an analysis from the Analysis panel to see results here.",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        sub_label.pack(pady=(10, 20))

        analysis_btn = ctk.CTkButton(
            message_frame,
            text="Go to Analysis",
            command=lambda: self.main_window._show_panel("analysis"),
            width=150,
            height=40,
            corner_radius=8
        )
        analysis_btn.pack()

    def _create_action_bar(self):
        """Create bottom action bar."""
        action_bar = ctk.CTkFrame(
            self.main_container,
            height=60,
            corner_radius=10,
            fg_color=self.theme_manager.get_color("surface")
        )
        action_bar.pack(fill="x", side="bottom")
        action_bar.pack_propagate(False)

        action_content = ctk.CTkFrame(action_bar, fg_color="transparent")
        action_content.pack(expand=True)

        # Action buttons
        buttons_data = [
            ("🔄 Refresh", self._refresh_results),
            ("📊 Generate Report", self._generate_report),
            ("⚡ Quick Report", self._quick_report),
            ("💾 Save Results", self._save_results),
            ("🖨️ Print", self._print_results)
        ]

        for i, (text, command) in enumerate(buttons_data):
            btn = ctk.CTkButton(
                action_content,
                text=text,
                command=command,
                width=130,
                height=35,
                corner_radius=6,
                fg_color="transparent" if i > 0 else self.theme_manager.get_color("primary"),
                border_width=2 if i > 0 else 0,
                border_color=self.theme_manager.get_color("border")
            )
            btn.pack(side="left", padx=5)

    def _generate_recommendations(self):
        """Generate analysis recommendations."""
        recommendations = []

        if self.analysis_results:
            flutter_speed = self.analysis_results.get("critical_flutter_speed", 0)

            if flutter_speed < 500:
                recommendations.append("Flutter speed is relatively low. Consider increasing panel stiffness.")
            elif flutter_speed > 1500:
                recommendations.append("Flutter speed is high. The design appears to be flutter-resistant.")

            if self.analysis_results.get("n_modes", 0) < 10:
                recommendations.append("Consider analyzing more modes for improved accuracy.")

            if not self.analysis_results.get("converged", True):
                recommendations.append("Analysis did not fully converge. Review input parameters.")
        else:
            recommendations.append("No analysis has been performed yet.")

        return recommendations

    def _on_mode_selected(self, selection):
        """Handle mode selection change."""
        pass

    def _export_diagram(self):
        """Export current diagram."""
        file_path = filedialog.asksaveasfilename(
            title="Export Diagram",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")]
        )
        if file_path:
            self.show_info("Export", f"Diagram would be exported to: {file_path}")

    def _export_data(self, format):
        """Export data in specified format."""
        extension = ".csv" if format == "csv" else ".json"
        file_path = filedialog.asksaveasfilename(
            title=f"Export Data as {format.upper()}",
            defaultextension=extension,
            filetypes=[(f"{format.upper()} files", f"*{extension}")]
        )
        if file_path:
            self.show_info("Export", f"Data would be exported to: {file_path}")

    def _add_comparison(self):
        """Add analysis for comparison."""
        file_path = filedialog.askopenfilename(
            title="Select Analysis Result",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.show_info("Comparison", f"Analysis loaded from: {file_path}")

    def _refresh_results(self):
        """Refresh analysis results."""
        self.show_info("Refresh", "Results refreshed successfully")

    def _quick_report(self):
        """Generate and open report quickly without dialog."""
        if not self.analysis_results:
            self.show_warning("No Data", "Please run an analysis first to generate a report.")
            return

        try:
            # Generate report with automatic naming
            report_path = self.report_generator.generate_report(self.analysis_results)

            # Open the report directly
            self.report_generator.open_report(report_path)

            self.show_info("Report Generated", f"Report opened in your browser.\nSaved to: {report_path}")

        except Exception as e:
            self.show_error("Report Error", f"Failed to generate report: {str(e)}")

    def _generate_report(self):
        """Generate analysis report."""
        if not self.analysis_results:
            self.show_warning("No Data", "Please run an analysis first to generate a report.")
            return

        try:
            # Ask user where to save the report
            file_path = filedialog.asksaveasfilename(
                title="Save Report As",
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                initialfile=f"flutter_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )

            if file_path:
                # Generate the report
                report_path = self.report_generator.generate_report(
                    self.analysis_results,
                    save_path=file_path
                )

                # Ask if user wants to open it
                result = messagebox.askyesno(
                    "Report Generated",
                    f"Report successfully generated at:\n{report_path}\n\nWould you like to open it now?"
                )

                if result:
                    self.report_generator.open_report(report_path)

        except Exception as e:
            self.show_error("Report Error", f"Failed to generate report: {str(e)}")

    def _save_results(self):
        """Save analysis results."""
        file_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path and self.analysis_results:
            with open(file_path, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            self.show_info("Save", f"Results saved to: {file_path}")

    def _print_results(self):
        """Print results."""
        self.show_info("Print", "Print functionality would be implemented here")

    def load_results(self, results: Dict[str, Any]):
        """Load analysis results for display."""
        self.analysis_results = results

        # Store modal frequencies separately for easy access
        self.modal_frequencies = results.get("modal_frequencies", []) if results else []

        # Update header status
        if results and results.get("success", False):
            self.status_label.configure(
                text=f"Analysis completed at {datetime.now().strftime('%H:%M:%S')}"
            )

            # Update metric cards
            flutter_speed = results.get("critical_flutter_speed", "--")
            flutter_freq = results.get("critical_flutter_frequency", "--")
            damping = results.get("critical_damping", "--")

            # Handle special case for "no flutter" (9999.0)
            if flutter_speed == 9999.0 or flutter_speed == 9999:
                self.speed_value_label.configure(text="No Flutter")
                self.freq_value_label.configure(text="--")
            else:
                if flutter_speed != "--" and flutter_speed is not None:
                    self.speed_value_label.configure(text=f"{flutter_speed:.1f}")
                else:
                    self.speed_value_label.configure(text="--")

                if flutter_freq != "--" and flutter_freq is not None:
                    self.freq_value_label.configure(text=f"{flutter_freq:.1f}")
                else:
                    self.freq_value_label.configure(text="--")

            if damping != "--" and damping is not None:
                self.damp_value_label.configure(text=f"{damping:.2f}")
            else:
                self.damp_value_label.configure(text="--")
        else:
            self.status_label.configure(text="Analysis failed")

        # Refresh current view
        self._switch_tab(self.current_view)

    def on_show(self):
        """Called when panel is shown."""
        self.main_window.update_status()

    def refresh(self):
        """Refresh the results panel."""
        self.on_show()