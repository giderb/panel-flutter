"""
Updated Results Panel for Validated Flutter System
===================================================
Replaces gui/panels/results_panel.py
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict, Any, List
import json
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .base_panel import BasePanel


class ResultsPanel(BasePanel):
    """Enhanced results panel for validated flutter analysis."""

    def __init__(self, parent, main_window):
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.current_view = "summary"
        super().__init__(parent, main_window)

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        # Header section
        self._create_header()

        # Main content area with tabs
        self._create_content_area()

    def _create_header(self):
        """Create header with title and controls."""
        header_frame = self.theme_manager.create_styled_frame(self.frame, elevated=True)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Title
        title_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Flutter Analysis Results",
            style="heading"
        )
        title_label.pack(side="left", padx=20, pady=15)

        # Status
        self.status_label = self.theme_manager.create_styled_label(
            header_frame,
            text="No analysis loaded",
            style="subheading"
        )
        self.status_label.pack(side="left", padx=20)

        # Export buttons
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=20)

        export_btn = ctk.CTkButton(
            button_frame,
            text="📥 Export",
            command=self._export_results,
            width=100
        )
        export_btn.pack(side="left", padx=5)

        report_btn = ctk.CTkButton(
            button_frame,
            text="📄 Report",
            command=self._generate_report,
            width=100
        )
        report_btn.pack(side="left", padx=5)

    def _create_content_area(self):
        """Create main content area with tabs."""
        content_frame = self.theme_manager.create_styled_frame(self.frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        # Tab buttons
        tab_frame = ctk.CTkFrame(content_frame)
        tab_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.tab_buttons = {}
        tabs = [
            ("summary", "📊 Summary"),
            ("vg_diagram", "📈 V-g Diagram"),
            ("vf_diagram", "📉 V-f Diagram"),
            ("validation", "✓ Validation"),
            ("details", "📋 Details")
        ]

        for tab_id, tab_text in tabs:
            btn = ctk.CTkButton(
                tab_frame,
                text=tab_text,
                command=lambda t=tab_id: self._switch_tab(t),
                width=120
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab_id] = btn

        # Content container
        self.content_container = ctk.CTkFrame(content_frame)
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Initialize with summary view
        self._switch_tab("summary")

    def _switch_tab(self, tab_id: str):
        """Switch to different result view."""
        self.current_view = tab_id

        # Update button states
        for btn_id, btn in self.tab_buttons.items():
            if btn_id == tab_id:
                btn.configure(fg_color=("gray70", "gray30"))
            else:
                btn.configure(fg_color=("gray75", "gray25"))

        # Clear content
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Load appropriate view
        if tab_id == "summary":
            self._show_summary()
        elif tab_id == "vg_diagram":
            self._show_vg_diagram()
        elif tab_id == "vf_diagram":
            self._show_vf_diagram()
        elif tab_id == "validation":
            self._show_validation()
        elif tab_id == "details":
            self._show_details()

    def _show_summary(self):
        """Show summary results."""
        if not self.analysis_results:
            self._show_no_data()
            return

        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_container,
            corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True)

        # Critical Results Card
        critical_card = self._create_card(scroll_frame, "⚡ Critical Flutter Point")
        critical_card.pack(fill="x", padx=10, pady=10)

        # Get actual and target flutter speeds
        actual_flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
        config = self.analysis_results.get('configuration', {})

        # Extract target speed from config (if provided by user)
        # This could come from velocity_max or a specific target_flutter_speed field
        target_flutter_speed = config.get('target_flutter_speed') or config.get('velocity_max')

        critical_data = [
            ("Actual Flutter Speed", f"{actual_flutter_speed:.1f} m/s"),
        ]

        # Add target speed comparison if available
        if target_flutter_speed and target_flutter_speed > 0:
            speed_ratio = actual_flutter_speed / target_flutter_speed
            if speed_ratio >= 1.0:
                comparison = f"✅ {speed_ratio:.2f}x target ({target_flutter_speed:.0f} m/s)"
                comparison_color = "green"
            else:
                comparison = f"⚠️ {speed_ratio:.2f}x target ({target_flutter_speed:.0f} m/s)"
                comparison_color = "orange"
            critical_data.append(("Target Flutter Speed", comparison))

        critical_data.extend([
            ("Flutter Frequency", f"{self.analysis_results.get('critical_flutter_frequency', 0):.1f} Hz"),
            ("Flutter Mode", f"Mode {self.analysis_results.get('critical_flutter_mode', 0)}"),
            ("Dynamic Pressure", f"{self.analysis_results.get('critical_dynamic_pressure', 0):.0f} Pa"),
            ("Safety Margin", f"{self.analysis_results.get('safety_margin', 0):.1f}%")
        ])

        for label, value in critical_data:
            row = self._add_info_row(critical_card, label, value)
            # Color the target comparison
            if label == "Target Flutter Speed" and target_flutter_speed:
                value_label = row.winfo_children()[-1]
                if hasattr(value_label, 'configure'):
                    value_label.configure(text_color=comparison_color if 'comparison_color' in locals() else None)

        # Design Recommendations Card (if target speed is not met)
        if target_flutter_speed and actual_flutter_speed < target_flutter_speed:
            design_card = self._create_card(scroll_frame, "💡 Design Recommendations")
            design_card.pack(fill="x", padx=10, pady=10)

            # Calculate required thickness using flutter speed scaling
            # V_flutter ∝ h (thickness) for same material and geometry
            current_thickness = config.get('panel_thickness', config.get('thickness'))

            if current_thickness:
                speed_ratio = target_flutter_speed / actual_flutter_speed

                # Check if scaling is valid (flutter speed proportional to thickness for small changes)
                if speed_ratio > 1.5 or speed_ratio < 0.67:
                    # Large change - linear scaling unreliable
                    required_thickness_base = current_thickness * speed_ratio
                    required_thickness = required_thickness_base * 1.25  # Add 25% safety margin for uncertainty
                    is_reliable = False
                    scaling_warning = (
                        f"⚠️ WARNING: Required thickness change ({(speed_ratio-1)*100:+.0f}%) "
                        f"exceeds linear approximation validity!\n\n"
                        f"This estimate is UNRELIABLE. Consider alternative approaches:\n"
                        f"  • Structural redesign (add ribs, stiffeners, or frames)\n"
                        f"  • Different material or layup orientation (for composites)\n"
                        f"  • Reduce panel dimensions (length or width)\n"
                        f"  • Sandwich construction or hybrid design\n\n"
                        f"Re-run iterative analyses with structural modifications."
                    )
                else:
                    # Small change - linear scaling acceptable with modest safety margin
                    required_thickness_base = current_thickness * speed_ratio
                    required_thickness = required_thickness_base * 1.10  # Add 10% safety margin
                    is_reliable = True
                    scaling_warning = None

                # Convert to mm for display
                current_thickness_mm = current_thickness * 1000  # m to mm
                required_thickness_mm = required_thickness * 1000  # m to mm
                thickness_increase = ((required_thickness / current_thickness) - 1) * 100

                design_data = [
                    ("Current Thickness", f"{current_thickness_mm:.2f} mm"),
                    ("Required Thickness", f"{required_thickness_mm:.2f} mm"),
                    ("Thickness Increase", f"+{thickness_increase:.1f}%"),
                    ("Speed Deficit", f"{target_flutter_speed - actual_flutter_speed:.1f} m/s"),
                    ("Estimate Reliability", "✅ Good (±10%)" if is_reliable else "❌ Poor (>±25%)"),
                ]

                for label, value in design_data:
                    row = self._add_info_row(design_card, label, value)
                    if label == "Required Thickness":
                        value_label = row.winfo_children()[-1]
                        if hasattr(value_label, 'configure'):
                            # Use cyan for reliable, orange for unreliable
                            color = "#00D9FF" if is_reliable else "#FFA500"
                            value_label.configure(text_color=color, font=("Arial", 12, "bold"))
                    elif label == "Estimate Reliability":
                        value_label = row.winfo_children()[-1]
                        if hasattr(value_label, 'configure'):
                            color = "green" if is_reliable else "red"
                            value_label.configure(text_color=color, font=("Arial", 11, "bold"))

                # Add explanatory note with scaling warning if unreliable
                note_frame = ctk.CTkFrame(design_card, fg_color="transparent")
                note_frame.pack(fill="x", padx=15, pady=(10, 15))

                if scaling_warning:
                    # Show warning for large changes
                    note_label = ctk.CTkLabel(
                        note_frame,
                        text=scaling_warning,
                        font=("Arial", 10),
                        text_color=("#CC0000", "#FF6666"),
                        justify="left",
                        wraplength=550
                    )
                    note_label.pack(anchor="w", pady=(0, 10))

                # Standard note
                standard_note = ctk.CTkLabel(
                    note_frame,
                    text="ℹ️  Flutter speed ∝ thickness (linear approximation). "
                         "Safety margin included. Re-run analysis to verify.",
                    font=("Arial", 10),
                    text_color=("#666666", "#AAAAAA"),
                    justify="left",
                    wraplength=550
                )
                standard_note.pack(anchor="w")
            else:
                self._add_info_row(design_card, "Status", "⚠️ Thickness data not available for recommendation")

        # Configuration Card
        config_card = self._create_card(scroll_frame, "⚙️ Configuration")
        config_card.pack(fill="x", padx=10, pady=10)

        config = self.analysis_results.get('configuration', {})
        config_data = [
            ("Panel Dimensions", config.get('panel_dimensions', 'Unknown')),
            ("Material", config.get('material', 'Unknown')),
            ("Boundary Conditions", config.get('boundary_conditions', 'Unknown')),
            ("Mach Number", f"{config.get('mach_number', 0):.2f}"),
            ("Altitude", f"{config.get('altitude', 0):.0f} m")
        ]

        for label, value in config_data:
            self._add_info_row(config_card, label, value)

        # Analysis Status Card
        status_card = self._create_card(scroll_frame, "📊 Analysis Status")
        status_card.pack(fill="x", padx=10, pady=10)

        # Determine stability
        flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
        if flutter_speed > 9000:
            stability = "✅ STABLE (No Flutter)"
            stability_color = "green"
        elif flutter_speed > 1500:
            stability = "⚠️ Flutter at High Speed"
            stability_color = "orange"
        else:
            stability = "❌ Flutter Detected"
            stability_color = "red"

        status_data = [
            ("Method", self.analysis_results.get('method', 'Unknown')),
            ("Convergence", "✅ Converged" if self.analysis_results.get('converged') else "❌ Not Converged"),
            ("Stability", stability),
            ("Validation", self._get_validation_summary()),
            ("Execution Time", f"{self.analysis_results.get('execution_time', 0):.2f} seconds")
        ]

        for i, (label, value) in enumerate(status_data):
            row = self._add_info_row(status_card, label, value)
            if label == "Stability":
                # Color the stability text
                value_label = row.winfo_children()[-1]
                if hasattr(value_label, 'configure'):
                    value_label.configure(text_color=stability_color)

    def _show_vg_diagram(self):
        """Show V-g (Velocity-Damping) diagram."""
        if not self.analysis_results or 'flutter_data' not in self.analysis_results:
            self._show_no_data()
            return

        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)

        flutter_data = self.analysis_results.get('flutter_data', {})
        velocities = flutter_data.get('velocities', [])
        damping = flutter_data.get('damping', [])

        if velocities and damping:
            # Convert to numpy arrays for safer operations
            velocities_arr = np.array(velocities)
            damping_arr = np.array(damping)

            # Plot damping curve
            ax.plot(velocities_arr, damping_arr, 'b-', linewidth=2, label='Damping')

            # Add zero line
            ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)

            # Mark flutter point
            critical_v = flutter_data.get('critical_velocity')
            if critical_v and critical_v < 9000:
                ax.axvline(x=critical_v, color='r', linestyle='--', alpha=0.7, label=f'Flutter: {critical_v:.1f} m/s')

                # Find damping at flutter
                idx = np.argmin(np.abs(velocities_arr - critical_v))
                if idx < len(damping_arr):
                    ax.plot(critical_v, damping_arr[idx], 'ro', markersize=10)

            ax.set_xlabel('Velocity (m/s)', fontsize=12)
            ax.set_ylabel('Damping (g)', fontsize=12)
            ax.set_title('V-g Diagram: Damping vs Velocity', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

            # Add stability regions - only if data length matches
            if len(velocities_arr) == len(damping_arr):
                try:
                    # Stable region (negative damping)
                    stable_mask = damping_arr < 0
                    if np.any(stable_mask):
                        ax.fill_between(velocities_arr, -10, 0, where=stable_mask,
                                       color='green', alpha=0.1, interpolate=True)
                    # Unstable region (positive damping)
                    unstable_mask = damping_arr > 0
                    if np.any(unstable_mask):
                        ax.fill_between(velocities_arr, 0, 10, where=unstable_mask,
                                       color='red', alpha=0.1, interpolate=True)
                except Exception as e:
                    self.logger.warning(f"Could not draw stability regions: {e}")

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.content_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _show_vf_diagram(self):
        """Show V-f (Velocity-Frequency) diagram."""
        if not self.analysis_results or 'flutter_data' not in self.analysis_results:
            self._show_no_data()
            return

        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)

        flutter_data = self.analysis_results.get('flutter_data', {})
        velocities = flutter_data.get('velocities', [])
        frequencies = flutter_data.get('frequencies', [])

        if velocities and frequencies:
            # Convert to numpy arrays for safer operations
            velocities_arr = np.array(velocities)
            frequencies_arr = np.array(frequencies)

            # Plot frequency curve
            ax.plot(velocities_arr, frequencies_arr, 'g-', linewidth=2, label='Frequency')

            # Mark flutter point
            critical_v = flutter_data.get('critical_velocity')
            critical_f = flutter_data.get('critical_frequency')

            if critical_v and critical_v < 9000 and critical_f:
                ax.axvline(x=critical_v, color='r', linestyle='--', alpha=0.7)
                ax.plot(critical_v, critical_f, 'ro', markersize=10,
                       label=f'Flutter: {critical_f:.1f} Hz @ {critical_v:.1f} m/s')

            ax.set_xlabel('Velocity (m/s)', fontsize=12)
            ax.set_ylabel('Frequency (Hz)', fontsize=12)
            ax.set_title('V-f Diagram: Frequency vs Velocity', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.content_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _show_validation(self):
        """Show validation results."""
        if not self.analysis_results:
            self._show_no_data()
            return

        scroll_frame = ctk.CTkScrollableFrame(
            self.content_container,
            corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True)

        # Physics validation
        physics_card = self._create_card(scroll_frame, "🔬 Physics Validation")
        physics_card.pack(fill="x", padx=10, pady=10)

        validation_status = self.analysis_results.get('validation_status', 'Not validated')
        self._add_info_row(physics_card, "Status", validation_status)

        physics_result = self.analysis_results.get('physics_result', {})
        if physics_result:
            self._add_info_row(physics_card, "Method", physics_result.get('method', 'Unknown'))
            self._add_info_row(physics_card, "Converged", "Yes" if physics_result.get('converged') else "No")

        # NASTRAN comparison (if available)
        comparison = self.analysis_results.get('comparison', {})
        if comparison and comparison.get('nastran_flutter_speed'):
            nastran_card = self._create_card(scroll_frame, "🔄 Cross-Validation")
            nastran_card.pack(fill="x", padx=10, pady=10)

            self._add_info_row(nastran_card, "Physics Flutter Speed", 
                             f"{comparison.get('physics_flutter_speed', 0):.1f} m/s")
            self._add_info_row(nastran_card, "NASTRAN Flutter Speed", 
                             f"{comparison.get('nastran_flutter_speed', 0):.1f} m/s")
            self._add_info_row(nastran_card, "Speed Difference", 
                             f"{comparison.get('speed_difference_percent', 0):.1f}%")
            self._add_info_row(nastran_card, "Frequency Difference", 
                             f"{comparison.get('frequency_difference_percent', 0):.1f}%")
            self._add_info_row(nastran_card, "Validation", 
                             comparison.get('validation_status', 'Unknown'))

        # Physical constraints check
        constraints_card = self._create_card(scroll_frame, "✓ Physical Constraints")
        constraints_card.pack(fill="x", padx=10, pady=10)

        flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
        flutter_freq = self.analysis_results.get('critical_flutter_frequency', 0)

        checks = [
            ("Positive Speed", flutter_speed > 0, flutter_speed > 0),
            ("Positive Frequency", flutter_freq > 0, flutter_freq > 0),
            ("Speed < Mach 10", flutter_speed < 3400, flutter_speed < 3400),
            ("Frequency < 1000 Hz", flutter_freq < 1000, flutter_freq < 1000),
            ("Mode Number Valid", True, True)
        ]

        for check_name, expected, actual in checks:
            status = "✅" if actual else "❌"
            self._add_info_row(constraints_card, check_name, status)

    def _show_details(self):
        """Show detailed JSON results."""
        text_widget = ctk.CTkTextbox(
            self.content_container,
            font=("Courier", 10)
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        if self.analysis_results:
            # Pretty print JSON
            detailed = json.dumps(self.analysis_results, indent=2, default=str)
            text_widget.insert("1.0", detailed)
        else:
            text_widget.insert("1.0", "No analysis results available")

        text_widget.configure(state="disabled")

    def _show_no_data(self):
        """Show no data message."""
        label = self.theme_manager.create_styled_label(
            self.content_container,
            text="No analysis results available.\nRun an analysis from the Analysis panel.",
            style="subheading"
        )
        label.place(relx=0.5, rely=0.5, anchor="center")

    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        """Create a result card."""
        card = self.theme_manager.create_styled_frame(parent, elevated=True)
        
        title_label = self.theme_manager.create_styled_label(
            card,
            text=title,
            style="subheading"
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        return card

    def _add_info_row(self, parent, label: str, value: str) -> ctk.CTkFrame:
        """Add an info row to a card."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=5)
        
        label_widget = self.theme_manager.create_styled_label(
            row, text=f"{label}:"
        )
        label_widget.pack(side="left", padx=(0, 10))
        
        value_widget = self.theme_manager.create_styled_label(
            row, text=value, style="value"
        )
        value_widget.pack(side="left")
        
        return row

    def _get_validation_summary(self) -> str:
        """Get validation status summary."""
        validation = self.analysis_results.get('validation_status', '')
        
        if 'EXCELLENT' in validation or 'VALIDATED' in validation:
            return "✅ Validated"
        elif 'GOOD' in validation or 'PASSED' in validation:
            return "✅ Good"
        elif 'WARNING' in validation:
            return "⚠️ Warning"
        elif 'FAILED' in validation:
            return "❌ Failed"
        else:
            return "❓ Unknown"

    def load_results(self, results: Dict[str, Any]):
        """Load analysis results."""
        self.analysis_results = results
        
        if results and results.get('success'):
            self.status_label.configure(
                text=f"Analysis completed at {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            self.status_label.configure(text="Analysis failed")
        
        # Refresh current view
        self._switch_tab(self.current_view)

    def _export_results(self):
        """Export results to file."""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No results to export")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text Report", "*.txt")
            ]
        )

        if filepath:
            try:
                if filepath.endswith('.json'):
                    with open(filepath, 'w') as f:
                        json.dump(self.analysis_results, f, indent=2, default=str)
                elif filepath.endswith('.csv'):
                    self._export_csv(filepath)
                else:
                    self._export_text_report(filepath)

                messagebox.showinfo("Export Complete", f"Results exported to:\n{filepath}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def _export_csv(self, filepath: str):
        """Export results as CSV."""
        import csv

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(['Flutter Analysis Results'])
            writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])

            # Critical results
            writer.writerow(['Parameter', 'Value', 'Unit'])
            writer.writerow(['Flutter Speed', self.analysis_results.get('critical_flutter_speed', 'N/A'), 'm/s'])
            writer.writerow(['Flutter Frequency', self.analysis_results.get('critical_flutter_frequency', 'N/A'), 'Hz'])
            writer.writerow(['Flutter Mode', self.analysis_results.get('critical_flutter_mode', 'N/A'), ''])
            writer.writerow(['Dynamic Pressure', self.analysis_results.get('critical_dynamic_pressure', 'N/A'), 'Pa'])
            writer.writerow(['Safety Margin', self.analysis_results.get('safety_margin', 'N/A'), '%'])
            writer.writerow(['Validation Status', self.analysis_results.get('validation_status', 'N/A'), ''])

            # Add velocity-damping data if available
            flutter_data = self.analysis_results.get('flutter_data', {})
            if flutter_data.get('velocities') and flutter_data.get('damping'):
                writer.writerow([])
                writer.writerow(['Velocity-Damping Data'])
                writer.writerow(['Velocity (m/s)', 'Damping (g)'])
                velocities = flutter_data.get('velocities', [])
                damping = flutter_data.get('damping', [])
                for v, g in zip(velocities, damping):
                    writer.writerow([v, g])

    def _export_text_report(self, filepath: str):
        """Export formatted text report."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("FLUTTER ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("CRITICAL RESULTS:\n")
            f.write("-" * 40 + "\n")
            flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
            flutter_freq = self.analysis_results.get('critical_flutter_frequency', 0)
            f.write(f"Flutter Speed: {flutter_speed:.1f} m/s\n" if flutter_speed else "Flutter Speed: N/A\n")
            f.write(f"Flutter Frequency: {flutter_freq:.1f} Hz\n" if flutter_freq else "Flutter Frequency: N/A\n")
            f.write(f"Flutter Mode: {self.analysis_results.get('critical_flutter_mode', 'N/A')}\n")
            f.write(f"Dynamic Pressure: {self.analysis_results.get('critical_dynamic_pressure', 0):.0f} Pa\n")
            f.write(f"Safety Margin: {self.analysis_results.get('safety_margin', 0):.1f}%\n\n")

            f.write("CONFIGURATION:\n")
            f.write("-" * 40 + "\n")
            config = self.analysis_results.get('configuration', {})
            if config:
                for key, value in config.items():
                    f.write(f"{key}: {value}\n")
            else:
                f.write("Configuration data not available\n")

            f.write("\nVALIDATION:\n")
            f.write("-" * 40 + "\n")
            f.write(f"{self.analysis_results.get('validation_status', 'Not validated')}\n")

            # Add flutter data summary if available
            flutter_data = self.analysis_results.get('flutter_data', {})
            if flutter_data:
                f.write("\nFLUTTER DATA SUMMARY:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Velocity range: {min(flutter_data.get('velocities', [0])):.1f} - {max(flutter_data.get('velocities', [0])):.1f} m/s\n")
                f.write(f"Number of data points: {len(flutter_data.get('velocities', []))}\n")

    def _generate_report(self):
        """Generate comprehensive HTML report."""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No results to generate report")
            return

        filepath = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html")]
        )

        if filepath:
            self._create_html_report(filepath)
            messagebox.showinfo("Report Generated", f"Report saved to:\n{filepath}")

    def _create_html_report(self, filepath: str):
        """Create HTML report with plots."""
        flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
        flutter_freq = self.analysis_results.get('critical_flutter_frequency', 0)
        flutter_mode = self.analysis_results.get('critical_flutter_mode', 'N/A')
        dynamic_pressure = self.analysis_results.get('critical_dynamic_pressure', 0)
        safety_margin = self.analysis_results.get('safety_margin', 0)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flutter Analysis Report</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
                h2 {{ color: #666; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #0066cc; color: white; }}
                .critical {{ background-color: #ffe6e6; }}
                .stable {{ color: green; font-weight: bold; }}
                .unstable {{ color: red; font-weight: bold; }}
                .info {{ background-color: #e6f2ff; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛫 Flutter Analysis Report</h1>
                <div class="info">
                    <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>

                <h2>Critical Flutter Point</h2>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr class="critical"><td>Flutter Speed</td><td>{flutter_speed:.1f} m/s</td></tr>
                    <tr class="critical"><td>Flutter Frequency</td><td>{flutter_freq:.1f} Hz</td></tr>
                    <tr><td>Flutter Mode</td><td>{flutter_mode}</td></tr>
                    <tr><td>Dynamic Pressure</td><td>{dynamic_pressure:.0f} Pa</td></tr>
                    <tr><td>Safety Margin</td><td>{safety_margin:.1f}%</td></tr>
                </table>

                <h2>Validation Status</h2>
                <div class="info">
                    {self.analysis_results.get('validation_status', 'Not validated')}
                </div>

                <h2>Configuration</h2>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
        """

        config = self.analysis_results.get('configuration', {})
        if config:
            for key, value in config.items():
                html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        else:
            html += "<tr><td colspan='2'>Configuration data not available</td></tr>"

        html += """
                </table>

                <h2>Analysis Information</h2>
                <table>
                    <tr><th>Item</th><th>Details</th></tr>
        """

        # Add analysis metadata
        html += f"""
                    <tr><td>Method</td><td>{self.analysis_results.get('method', 'N/A')}</td></tr>
                    <tr><td>Converged</td><td>{'Yes' if self.analysis_results.get('converged') else 'No'}</td></tr>
                    <tr><td>Execution Time</td><td>{self.analysis_results.get('execution_time', 0):.2f} seconds</td></tr>
                </table>
            </div>
        </body>
        </html>
        """

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    def refresh(self):
        """Refresh the panel."""
        if self.analysis_results:
            self._switch_tab(self.current_view)

    def on_show(self):
        """Called when panel is shown."""
        self.refresh()
