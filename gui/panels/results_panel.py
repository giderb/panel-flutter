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
        """Show comprehensive summary results with enhanced outputs."""
        if not self.analysis_results:
            self._show_no_data()
            return

        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_container,
            corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True)

        # Get key data
        config = self.analysis_results.get('configuration', {})
        actual_flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
        flutter_freq = self.analysis_results.get('critical_flutter_frequency', 0)
        flutter_mode = self.analysis_results.get('critical_flutter_mode', 0)
        dynamic_pressure = self.analysis_results.get('critical_dynamic_pressure', 0)
        converged = self.analysis_results.get('converged', True)
        damping_ratio = self.analysis_results.get('critical_damping_ratio', 0)

        # Get physics result for additional parameters
        physics_result = self.analysis_results.get('physics_result', {})
        reduced_frequency = physics_result.get('reduced_frequency', 0)
        uncertainty_upper = physics_result.get('uncertainty_upper', 0)
        uncertainty_lower = physics_result.get('uncertainty_lower', 0)

        # Calculate flight condition parameters
        mach_number = config.get('mach_number', 0)
        altitude = config.get('altitude', 0)
        temperature = config.get('temperature', 288.15)
        air_density = config.get('air_density', 1.225)
        target_flutter_speed = None
        if mach_number > 0 and altitude is not None:
            target_flutter_speed = self._calculate_true_airspeed(mach_number, altitude)

        # === CARD 1: FLIGHT SAFETY STATUS (Big, Bold Answer) ===
        safety_card = self._create_card(scroll_frame, "🛡️ Flight Safety Assessment")
        safety_card.pack(fill="x", padx=10, pady=10)

        # Calculate clearance
        if target_flutter_speed and target_flutter_speed > 0 and actual_flutter_speed < 900000:
            flutter_margin = ((actual_flutter_speed / target_flutter_speed) - 1.0) * 100
            envelope_cleared = flutter_margin >= 15.0  # MIL-STD requires 15% minimum margin

            clearance_status = "✅ CLEARED FOR FLIGHT" if envelope_cleared else "❌ NOT CLEARED"
            clearance_color = "green" if envelope_cleared else "red"

            margin_str = f"{flutter_margin:+.1f}%" if flutter_margin >= 0 else f"{flutter_margin:.1f}%"
            margin_color = "green" if flutter_margin >= 15 else ("orange" if flutter_margin >= 0 else "red")

            safety_data = [
                ("Clearance Status", clearance_status),
                ("Flight Condition", f"M = {mach_number:.2f} @ {altitude:.0f} m"),
                ("Required Flutter Speed", f"{target_flutter_speed:.1f} m/s (dive speed)"),
                ("Predicted Flutter Speed", f"{actual_flutter_speed:.1f} m/s"),
                ("Safety Margin", margin_str + " " + ("(PASS)" if flutter_margin >= 15 else "(FAIL)"))
            ]

            for label, value in safety_data:
                row = self._add_info_row(safety_card, label, value)
                value_label = row.winfo_children()[-1]
                if label == "Clearance Status" and hasattr(value_label, 'configure'):
                    value_label.configure(
                        text_color=clearance_color,
                        font=self.theme_manager.get_font(size=14, weight="bold")
                    )
                elif label == "Safety Margin" and hasattr(value_label, 'configure'):
                    value_label.configure(
                        text_color=margin_color,
                        font=self.theme_manager.get_body_font(weight="bold")
                    )
        elif actual_flutter_speed >= 900000:
            # No flutter found - panel is stable
            safety_data = [
                ("Clearance Status", "✅ NO FLUTTER DETECTED"),
                ("Analysis Result", f"Panel is STABLE across tested range"),
                ("Flight Condition", f"M = {mach_number:.2f} @ {altitude:.0f} m"),
                ("Maximum Tested Speed", f"{config.get('velocity_max', 2500):.0f} m/s"),
            ]
            for label, value in safety_data:
                row = self._add_info_row(safety_card, label, value)
                if label == "Clearance Status":
                    value_label = row.winfo_children()[-1]
                    if hasattr(value_label, 'configure'):
                        value_label.configure(
                            text_color="green",
                            font=self.theme_manager.get_font(size=14, weight="bold")
                        )
        else:
            # No target speed specified
            safety_data = [
                ("Predicted Flutter Speed", f"{actual_flutter_speed:.1f} m/s"),
                ("Note", "⚠️ No flight condition specified - cannot assess clearance")
            ]
            for label, value in safety_data:
                self._add_info_row(safety_card, label, value)

        # Convergence warning if needed
        if not converged:
            warning_row = ctk.CTkFrame(safety_card, fg_color="transparent")
            warning_row.pack(fill="x", padx=15, pady=5)
            warning_label = self.theme_manager.create_styled_label(
                warning_row,
                text="⚠️ WARNING: Analysis did not converge - increase velocity range!",
                style="body"
            )
            warning_label.configure(text_color="orange")
            warning_label.pack(anchor="w")

        # === CARD 2: FLUTTER CHARACTERISTICS (Technical Data) ===
        if actual_flutter_speed < 900000:  # Only show if flutter was found
            flutter_card = self._create_card(scroll_frame, "⚡ Flutter Characteristics")
            flutter_card.pack(fill="x", padx=10, pady=10)

            flutter_data = [
                ("Flutter Speed", f"{actual_flutter_speed:.1f} m/s ({actual_flutter_speed*3.6:.1f} km/h)"),
                ("Flutter Frequency", f"{flutter_freq:.1f} Hz"),
                ("Critical Mode", f"Mode {flutter_mode}"),
                ("Dynamic Pressure", f"{dynamic_pressure:.0f} Pa ({dynamic_pressure/1000:.1f} kPa)" if dynamic_pressure > 0 else "N/A")
            ]

            # Add uncertainty bounds if available
            if uncertainty_upper > 0 or uncertainty_lower < 0:
                flutter_data.append(
                    ("Uncertainty Bounds", f"+{uncertainty_upper:.1f}% / {uncertainty_lower:.1f}%")
                )

            for label, value in flutter_data:
                row = self._add_info_row(flutter_card, label, value)
                # Highlight uncertainty bounds in orange if significant
                if label == "Uncertainty Bounds":
                    value_label = row.winfo_children()[-1]
                    if hasattr(value_label, 'configure'):
                        value_label.configure(
                            text_color="orange",
                            font=self.theme_manager.get_body_font(weight="bold")
                        )

        # === CARD 3: ANALYSIS QUALITY (Confidence & Validation) ===
        quality_card = self._create_card(scroll_frame, "✓ Analysis Quality")
        quality_card.pack(fill="x", padx=10, pady=10)

        # Get validation data
        comparison = self.analysis_results.get('comparison', {})
        nastran_speed = comparison.get('nastran_flutter_speed')
        confidence_level = self._determine_confidence_level()

        # Get friendly method name
        raw_method = self.analysis_results.get('method', 'Unknown')
        friendly_method = self._get_friendly_method_name(raw_method)

        quality_data = [
            ("Analysis Method", friendly_method),
            ("Convergence", "✅ Converged" if converged else "❌ Not Converged"),
        ]

        for label, value in quality_data:
            self._add_info_row(quality_card, label, value)

        # Add NASTRAN comparison table if available
        if nastran_speed and nastran_speed < 900000:
            # Create comparison header
            comparison_header = ctk.CTkFrame(quality_card, fg_color="transparent")
            comparison_header.pack(fill="x", padx=15, pady=(10, 5))

            header_label = self.theme_manager.create_styled_label(
                comparison_header,
                text="NASTRAN vs. Physics Comparison:",
                style="body"
            )
            header_label.configure(font=self.theme_manager.get_body_font(weight="bold"))
            header_label.pack(anchor="w")

            # Create comparison table
            comparison_table = ctk.CTkFrame(quality_card, fg_color="transparent")
            comparison_table.pack(fill="x", padx=15, pady=5)

            # Header row
            header_row = ctk.CTkFrame(comparison_table, fg_color="transparent")
            header_row.pack(fill="x", pady=2)

            for col_text in ["Parameter", "Physics", "NASTRAN", "Δ%", "Status"]:
                col_label = self.theme_manager.create_styled_label(
                    header_row, text=col_text
                )
                col_label.configure(font=self.theme_manager.get_body_font(weight="bold"))
                col_label.pack(side="left", padx=5, expand=True)

            # Data row
            speed_diff = comparison.get('speed_difference_percent', 0)

            # Determine status
            if abs(speed_diff) < 5.0:
                status_text = "✅ EXCELLENT"
                status_color = "green"
            elif abs(speed_diff) < 15.0:
                status_text = "⚠️ ACCEPTABLE"
                status_color = "orange"
            else:
                status_text = "❌ INVESTIGATE"
                status_color = "red"

            data_row = ctk.CTkFrame(comparison_table, fg_color="transparent")
            data_row.pack(fill="x", pady=2)

            values = [
                "Flutter Speed",
                f"{actual_flutter_speed:.1f} m/s",
                f"{nastran_speed:.1f} m/s",
                f"{speed_diff:+.1f}%",
                status_text
            ]

            for i, val_text in enumerate(values):
                val_label = self.theme_manager.create_styled_label(
                    data_row, text=val_text
                )
                if i == 4:  # Status column
                    val_label.configure(text_color=status_color)
                val_label.pack(side="left", padx=5, expand=True)

        # Overall confidence
        confidence_row = self._add_info_row(quality_card, "Overall Confidence", confidence_level)
        value_label = confidence_row.winfo_children()[-1]
        if hasattr(value_label, 'configure'):
            if "HIGH" in confidence_level:
                value_label.configure(text_color="green", font=self.theme_manager.get_body_font(weight="bold"))
            elif "MEDIUM" in confidence_level:
                value_label.configure(text_color="orange")
            elif "LOW" in confidence_level:
                value_label.configure(text_color="red", font=self.theme_manager.get_body_font(weight="bold"))

        # === CARD 4: DESIGN GUIDANCE (Only if clearance failed) ===
        if target_flutter_speed and actual_flutter_speed < target_flutter_speed and actual_flutter_speed < 900000:
            design_card = self._create_card(scroll_frame, "💡 Design Recommendations")
            design_card.pack(fill="x", padx=10, pady=10)

            current_thickness = config.get('panel_thickness', config.get('thickness'))

            if current_thickness:
                speed_ratio = target_flutter_speed / actual_flutter_speed
                required_thickness = current_thickness * speed_ratio * 1.15  # 15% safety margin
                current_thickness_mm = current_thickness * 1000
                required_thickness_mm = required_thickness * 1000
                thickness_increase = ((required_thickness / current_thickness) - 1) * 100

                # Determine if estimate is reliable
                is_reliable = 0.67 <= speed_ratio <= 1.5

                design_data = [
                    ("Recommended Action", "INCREASE THICKNESS" if is_reliable else "REDESIGN REQUIRED"),
                    ("Current Thickness", f"{current_thickness_mm:.2f} mm"),
                    ("Suggested Thickness", f"{required_thickness_mm:.2f} mm (+{thickness_increase:.1f}%)"),
                ]

                if not is_reliable:
                    design_data.append(
                        ("Alternative Options", "Change material, add stiffeners, or reduce panel size")
                    )

                for label, value in design_data:
                    row = self._add_info_row(design_card, label, value)
                    if label == "Recommended Action":
                        value_label = row.winfo_children()[-1]
                        if hasattr(value_label, 'configure'):
                            color = "orange" if is_reliable else "red"
                            value_label.configure(text_color=color, font=self.theme_manager.get_body_font(weight="bold"))
            else:
                self._add_info_row(design_card, "Status", "⚠️ Insufficient data for recommendations")

        # === CARD 5: STRUCTURAL PROPERTIES ===
        struct_card = self._create_card(scroll_frame, "🔧 Structural Properties")
        struct_card.pack(fill="x", padx=10, pady=10)

        # Parse panel dimensions from config string (e.g., "1000.0x500.0x1.5mm")
        panel_dims_str = config.get('panel_dimensions', '')
        material_str = config.get('material', '')

        # Extract numerical values
        length, width, thickness_mm = self._parse_dimensions(panel_dims_str)
        youngs_modulus, poisson_ratio, density = self._parse_material(material_str)

        # Calculate structural properties
        thickness_m = thickness_mm / 1000.0 if thickness_mm else config.get('thickness', 0.0015)
        panel_mass = density * length * width * thickness_m if (length and width and thickness_m and density) else 0
        flexural_rigidity = (youngs_modulus * thickness_m**3) / (12 * (1 - poisson_ratio**2)) if youngs_modulus else 0
        aspect_ratio = length / width if (length and width and width > 0) else 0
        thickness_ratio = thickness_m / length if (length and thickness_m) else 0

        struct_data = [
            ("Panel Dimensions", f"{length*1000:.1f} × {width*1000:.1f} × {thickness_mm:.2f} mm"),
            ("Panel Mass", f"{panel_mass:.3f} kg" if panel_mass > 0 else "N/A"),
            ("Aspect Ratio (L/W)", f"{aspect_ratio:.2f}" if aspect_ratio > 0 else "N/A"),
            ("Thickness Ratio (t/L)", f"{thickness_ratio*1000:.3f} ×10⁻³" if thickness_ratio > 0 else "N/A"),
            ("Flexural Rigidity (D)", f"{flexural_rigidity:.2f} N·m" if flexural_rigidity > 0 else "N/A"),
            ("Boundary Condition", config.get('boundary_conditions', 'N/A')),
        ]

        for label, value in struct_data:
            self._add_info_row(struct_card, label, value)

        # === CARD 6: AERODYNAMIC PARAMETERS ===
        aero_card = self._create_card(scroll_frame, "✈️ Aerodynamic Parameters")
        aero_card.pack(fill="x", padx=10, pady=10)

        # Calculate speed of sound and Reynolds number
        gamma_air = 1.4
        R_gas = 287.05  # J/(kg·K)
        speed_of_sound = (gamma_air * R_gas * temperature)**0.5 if temperature > 0 else 340.0
        true_airspeed = mach_number * speed_of_sound

        # Dynamic viscosity (Sutherland's formula)
        T_ref = 288.15  # K
        mu_ref = 1.789e-5  # Pa·s at T_ref
        S = 110.4  # Sutherland constant for air (K)
        dynamic_viscosity = mu_ref * (temperature / T_ref)**1.5 * (T_ref + S) / (temperature + S)

        # Reynolds number based on panel length
        reynolds_number = (air_density * true_airspeed * length) / dynamic_viscosity if (length and dynamic_viscosity > 0) else 0

        # Reduced frequency k = ω*c/(2*V)
        if actual_flutter_speed > 0 and flutter_freq > 0:
            omega = 2 * np.pi * flutter_freq
            reduced_freq_calc = (omega * length) / (2 * actual_flutter_speed)
        else:
            reduced_freq_calc = reduced_frequency if reduced_frequency else 0

        aero_data = [
            ("Mach Number", f"{mach_number:.3f}"),
            ("Altitude", f"{altitude:.0f} m ({altitude/1000:.1f} km)"),
            ("Temperature", f"{temperature:.1f} K ({temperature-273.15:.1f}°C)"),
            ("Air Density", f"{air_density:.3f} kg/m³"),
            ("Speed of Sound", f"{speed_of_sound:.1f} m/s"),
            ("True Airspeed", f"{true_airspeed:.1f} m/s"),
            ("Dynamic Pressure", f"{dynamic_pressure:.0f} Pa ({dynamic_pressure/1000:.1f} kPa)"),
            ("Reynolds Number", f"{reynolds_number:.2e}" if reynolds_number > 0 else "N/A"),
            ("Reduced Frequency (k)", f"{reduced_freq_calc:.4f}" if reduced_freq_calc else "N/A"),
        ]

        for label, value in aero_data:
            self._add_info_row(aero_card, label, value)

        # === CARD 7: NON-DIMENSIONAL PARAMETERS ===
        nondim_card = self._create_card(scroll_frame, "📐 Non-Dimensional Parameters")
        nondim_card.pack(fill="x", padx=10, pady=10)

        # Mass ratio μ = (ρ_panel * h) / (ρ_air * L)
        mass_ratio = (density * thickness_m) / (air_density * length) if (density and thickness_m and air_density and length) else 0

        # Flutter parameter λ = (q * L⁴) / (D * m * β)
        # where q = dynamic pressure, m = mass per area, β = √(M²-1)
        if mach_number > 1.0:
            beta = (mach_number**2 - 1.0)**0.5
        else:
            beta = 0.1  # Placeholder for subsonic

        mass_per_area = density * thickness_m if (density and thickness_m) else 0
        if flexural_rigidity and mass_per_area and beta and actual_flutter_speed > 0:
            q_flutter = 0.5 * air_density * actual_flutter_speed**2
            flutter_param = (q_flutter * length**4) / (flexural_rigidity * mass_per_area * beta)
        else:
            flutter_param = 0

        # Dynamic pressure coefficient
        q_coeff = dynamic_pressure / (0.5 * air_density * speed_of_sound**2) if speed_of_sound > 0 else 0

        nondim_data = [
            ("Mass Ratio (μ)", f"{mass_ratio:.3f}" if mass_ratio > 0 else "N/A"),
            ("Flutter Parameter (λ)", f"{flutter_param:.1f}" if flutter_param > 0 else "N/A"),
            ("Compressibility (β)", f"{beta:.3f}" if mach_number > 1.0 else f"{(1-mach_number**2)**0.5:.3f} (subsonic)"),
            ("Dynamic Press. Coeff.", f"{q_coeff:.3f}" if q_coeff > 0 else "N/A"),
            ("Damping Ratio (ζ)", f"{damping_ratio:.4f}" if damping_ratio != 0 else "~0 (at flutter)"),
        ]

        for label, value in nondim_data:
            self._add_info_row(nondim_card, label, value)

        # === CARD 8: MODAL ANALYSIS ===
        if actual_flutter_speed < 900000:  # Only show if flutter found
            modal_card = self._create_card(scroll_frame, "🎵 Modal Analysis")
            modal_card.pack(fill="x", padx=10, pady=10)

            # Try to extract natural frequencies if available
            # For now, calculate first mode analytically
            if flexural_rigidity and mass_per_area and length and width:
                omega_11 = (np.pi**2 * (flexural_rigidity / mass_per_area)**0.5 *
                           ((1/length)**2 + (1/width)**2))
                freq_11 = omega_11 / (2 * np.pi)
            else:
                freq_11 = 0

            modal_data = [
                ("Critical Flutter Mode", f"Mode {flutter_mode}"),
                ("Flutter Frequency", f"{flutter_freq:.2f} Hz"),
                ("1st Natural Freq. (Est.)", f"{freq_11:.2f} Hz" if freq_11 > 0 else "N/A"),
                ("Frequency Ratio", f"{flutter_freq/freq_11:.2f}" if (freq_11 > 0 and flutter_freq > 0) else "N/A"),
            ]

            for label, value in modal_data:
                self._add_info_row(modal_card, label, value)

        # === CARD 9: CORRECTIONS & ADJUSTMENTS ===
        if physics_result:
            corr_card = self._create_card(scroll_frame, "⚙️ Corrections & Adjustments")
            corr_card.pack(fill="x", padx=10, pady=10)

            # Extract correction factors
            transonic_factor = physics_result.get('transonic_correction_factor', 1.0)
            temp_factor = physics_result.get('temperature_degradation_factor', 1.0)
            uncorrected_speed = physics_result.get('uncorrected_flutter_speed', actual_flutter_speed)
            wall_temp = physics_result.get('wall_temperature', temperature)

            # Uncertainty bounds
            uncertainty_upper = physics_result.get('uncertainty_upper', 0)
            uncertainty_lower = physics_result.get('uncertainty_lower', 0)

            corr_data = []

            if uncorrected_speed > 0 and uncorrected_speed != actual_flutter_speed:
                corr_data.append(("Uncorrected Flutter Speed", f"{uncorrected_speed:.1f} m/s"))
                corr_data.append(("Corrected Flutter Speed", f"{actual_flutter_speed:.1f} m/s"))

            if transonic_factor != 1.0:
                reduction = (1.0 - transonic_factor) * 100
                corr_data.append(("Transonic Correction", f"{transonic_factor:.4f} ({reduction:.1f}% reduction)"))

            if temp_factor != 1.0:
                degradation = (1.0 - temp_factor) * 100
                corr_data.append(("Temperature Degradation", f"{temp_factor:.4f} ({degradation:.1f}% loss)"))
                corr_data.append(("Wall Temperature", f"{wall_temp:.1f} K ({wall_temp-273.15:.1f}°C)"))

            if uncertainty_upper > 0 or uncertainty_lower < 0:
                corr_data.append(("Uncertainty Bounds", f"+{uncertainty_upper:.1f}% / {uncertainty_lower:.1f}%"))

            if corr_data:
                for label, value in corr_data:
                    self._add_info_row(corr_card, label, value)
            else:
                self._add_info_row(corr_card, "Status", "No corrections applied (baseline analysis)")

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
        """Show comprehensive validation results."""
        if not self.analysis_results:
            self._show_no_data()
            return

        scroll_frame = ctk.CTkScrollableFrame(
            self.content_container,
            corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True)

        # Get data
        config = self.analysis_results.get('configuration', {})
        flutter_speed = self.analysis_results.get('critical_flutter_speed', 0)
        flutter_freq = self.analysis_results.get('critical_flutter_frequency', 0)
        flutter_mode = self.analysis_results.get('critical_flutter_mode', 0)
        dynamic_pressure = self.analysis_results.get('critical_dynamic_pressure', 0)

        mach_number = config.get('mach_number', 0)
        temperature = config.get('temperature', 288.15)

        # Physics validation
        physics_card = self._create_card(scroll_frame, "🔬 Physics Validation")
        physics_card.pack(fill="x", padx=10, pady=10)

        validation_status = self.analysis_results.get('validation_status', 'Not validated')
        self._add_info_row(physics_card, "Status", validation_status)

        physics_result = self.analysis_results.get('physics_result', {})
        if physics_result:
            self._add_info_row(physics_card, "Method", physics_result.get('method', 'Unknown'))
            converged = physics_result.get('converged', False)
            conv_status = "✅ Yes" if converged else "❌ No"
            self._add_info_row(physics_card, "Converged", conv_status)

        # NASTRAN comparison (if available)
        comparison = self.analysis_results.get('comparison', {})
        if comparison and comparison.get('nastran_flutter_speed'):
            nastran_card = self._create_card(scroll_frame, "🔄 Cross-Validation (NASTRAN)")
            nastran_card.pack(fill="x", padx=10, pady=10)

            phys_speed = comparison.get('physics_flutter_speed', 0)
            nast_speed = comparison.get('nastran_flutter_speed', 0)
            speed_diff = comparison.get('speed_difference_percent', 0)
            freq_diff = comparison.get('frequency_difference_percent', 0)

            self._add_info_row(nastran_card, "Physics Flutter Speed", f"{phys_speed:.1f} m/s")
            self._add_info_row(nastran_card, "NASTRAN Flutter Speed", f"{nast_speed:.1f} m/s")

            # Color code speed difference
            speed_diff_str = f"{speed_diff:.1f}%"
            if speed_diff < 5:
                speed_diff_str += " (EXCELLENT)"
            elif speed_diff < 10:
                speed_diff_str += " (GOOD)"
            elif speed_diff < 20:
                speed_diff_str += " (ACCEPTABLE)"
            else:
                speed_diff_str += " (REVIEW)"

            self._add_info_row(nastran_card, "Speed Difference", speed_diff_str)
            self._add_info_row(nastran_card, "Frequency Difference", f"{freq_diff:.1f}%")
            self._add_info_row(nastran_card, "Validation", comparison.get('validation_status', 'Unknown'))

        # Physical constraints check
        constraints_card = self._create_card(scroll_frame, "✓ Physical Constraints")
        constraints_card.pack(fill="x", padx=10, pady=10)

        # Speed of sound for Mach 10 check
        gamma_air = 1.4
        R_gas = 287.05
        speed_of_sound = (gamma_air * R_gas * temperature)**0.5
        mach_10_speed = 10 * speed_of_sound

        checks = [
            ("Positive Flutter Speed", flutter_speed > 0),
            ("Positive Flutter Frequency", flutter_freq > 0),
            ("Speed < Mach 10", flutter_speed < mach_10_speed),
            ("Frequency < 1000 Hz", flutter_freq < 1000),
            ("Frequency > 1 Hz", flutter_freq > 1 or flutter_speed > 900000),
            ("Mode Number Valid (1-20)", 1 <= flutter_mode <= 20 or flutter_mode == 0),
            ("Dynamic Pressure Positive", dynamic_pressure > 0 or flutter_speed > 900000),
        ]

        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            self._add_info_row(constraints_card, check_name, status)

        # Dimensional analysis check
        dim_card = self._create_card(scroll_frame, "📏 Dimensional Analysis")
        dim_card.pack(fill="x", padx=10, pady=10)

        # Extract properties
        panel_dims_str = config.get('panel_dimensions', '')
        material_str = config.get('material', '')
        length, width, thickness_mm = self._parse_dimensions(panel_dims_str)
        youngs_modulus, poisson_ratio, density = self._parse_material(material_str)

        if length and width and thickness_mm and youngs_modulus and density:
            thickness_m = thickness_mm / 1000.0

            # Calculate characteristic velocity using plate theory
            # V_char = sqrt(D / (ρ*h)) / L
            flexural_rigidity = (youngs_modulus * thickness_m**3) / (12 * (1 - poisson_ratio**2))
            mass_per_area = density * thickness_m
            char_velocity = (flexural_rigidity / mass_per_area)**0.5 / length

            # Flutter speed should be order of magnitude of characteristic velocity
            if flutter_speed > 0 and flutter_speed < 900000:
                ratio = flutter_speed / char_velocity
                dim_check = 0.1 < ratio < 10.0  # Within order of magnitude

                dim_data = [
                    ("Characteristic Velocity", f"{char_velocity:.1f} m/s"),
                    ("Flutter / Char. Velocity", f"{ratio:.2f}"),
                    ("Dimensional Check", "✅ PASS" if dim_check else "⚠️ REVIEW"),
                ]

                for label, value in dim_data:
                    self._add_info_row(dim_card, label, value)
            else:
                self._add_info_row(dim_card, "Status", "Flutter not found in range")
        else:
            self._add_info_row(dim_card, "Status", "Insufficient data for dimensional analysis")

        # Regime validity check
        regime_card = self._create_card(scroll_frame, "🌐 Aerodynamic Regime Validity")
        regime_card.pack(fill="x", padx=10, pady=10)

        method = physics_result.get('method', 'Unknown')

        regime_checks = []

        if 'piston' in method.lower():
            # Piston theory valid for M >= 1.5
            if mach_number >= 1.5:
                regime_checks.append(("Piston Theory Regime", "✅ Valid (M ≥ 1.5)"))
            elif mach_number >= 1.2:
                regime_checks.append(("Piston Theory Regime", "⚠️ Marginal (M ≥ 1.2, prefer 1.5+)"))
            else:
                regime_checks.append(("Piston Theory Regime", "❌ Invalid (M < 1.2, use DLM)"))

        if 'doublet' in method.lower() or 'dlm' in method.lower():
            # DLM valid for M < 1.5
            if mach_number < 1.0:
                regime_checks.append(("DLM Regime", "✅ Valid (M < 1.0)"))
            elif mach_number < 1.5:
                regime_checks.append(("DLM Regime", "⚠️ Transonic (1.0 ≤ M < 1.5)"))
            else:
                regime_checks.append(("DLM Regime", "❌ Invalid (M ≥ 1.5, use Piston)"))

        # Transonic warning
        if 0.8 <= mach_number <= 1.2:
            regime_checks.append(("Transonic Effects", "⚠️ Significant (±15-25% error expected)"))

        # Hypersonic warning
        if mach_number > 5.0:
            regime_checks.append(("Hypersonic Effects", "⚠️ Piston Theory degrades (M > 5)"))

        if regime_checks:
            for label, value in regime_checks:
                self._add_info_row(regime_card, label, value)
        else:
            self._add_info_row(regime_card, "Method", method)

    def _show_details(self):
        """Show detailed JSON results."""
        text_widget = ctk.CTkTextbox(
            self.content_container,
            font=self.theme_manager.get_monospace_font()
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

    def _determine_confidence_level(self) -> str:
        """Determine overall confidence level in results."""
        converged = self.analysis_results.get('converged', False)
        validation_status = self.analysis_results.get('validation_status', '')
        comparison = self.analysis_results.get('comparison', {})
        nastran_available = comparison.get('nastran_flutter_speed') is not None

        # High confidence: Converged + NASTRAN validated + good agreement
        if converged and nastran_available:
            speed_diff = abs(comparison.get('speed_difference_percent', 100))
            if speed_diff < 5.0:
                return "✅ HIGH (NASTRAN validated)"
            elif speed_diff < 15.0:
                return "⚠️ MEDIUM (NASTRAN differs by {:.1f}%)".format(speed_diff)
            else:
                return "❌ LOW (NASTRAN differs by {:.1f}%)".format(speed_diff)

        # Medium confidence: Converged + physics validation
        elif converged:
            if 'EXCELLENT' in validation_status or 'VALIDATED' in validation_status:
                return "✅ MEDIUM (Physics validated)"
            elif 'GOOD' in validation_status:
                return "⚠️ MEDIUM (Physics check passed)"
            else:
                return "⚠️ LOW (No validation)"

        # Low confidence: Not converged
        else:
            return "❌ LOW (Did not converge)"

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

    def _parse_dimensions(self, dims_str: str) -> tuple:
        """
        Parse panel dimensions from config string.

        Args:
            dims_str: String like "1000.0x500.0x1.5mm"

        Returns:
            Tuple of (length_m, width_m, thickness_mm)
        """
        try:
            if 'x' in dims_str and 'mm' in dims_str:
                # Remove 'mm' suffix
                nums_str = dims_str.replace('mm', '').strip()
                parts = nums_str.split('x')
                if len(parts) >= 3:
                    length_mm = float(parts[0])
                    width_mm = float(parts[1])
                    thickness_mm = float(parts[2])
                    return length_mm / 1000.0, width_mm / 1000.0, thickness_mm
        except (ValueError, IndexError):
            pass
        return 0, 0, 0

    def _parse_material(self, material_str: str) -> tuple:
        """
        Parse material properties from config string.

        Args:
            material_str: String like "E=71.7GPa, nu=0.33, rho=2810kg/m3"

        Returns:
            Tuple of (youngs_modulus_Pa, poisson_ratio, density_kg_m3)
        """
        try:
            E, nu, rho = 71.7e9, 0.33, 2810  # Defaults

            if 'E=' in material_str:
                # Extract Young's modulus
                e_part = material_str.split('E=')[1].split(',')[0].strip()
                if 'GPa' in e_part:
                    E = float(e_part.replace('GPa', '').strip()) * 1e9

            if 'nu=' in material_str:
                # Extract Poisson's ratio
                nu_part = material_str.split('nu=')[1].split(',')[0].strip()
                nu = float(nu_part)

            if 'rho=' in material_str:
                # Extract density
                rho_part = material_str.split('rho=')[1].split('kg/m')[0].strip()
                rho = float(rho_part)

            return E, nu, rho
        except (ValueError, IndexError):
            return 71.7e9, 0.33, 2810  # Default aluminum values

    def _calculate_true_airspeed(self, mach_number: float, altitude: float) -> float:
        """
        Calculate true airspeed from Mach number and altitude using standard atmosphere.

        Args:
            mach_number: Mach number (dimensionless)
            altitude: Altitude in meters

        Returns:
            True airspeed in m/s

        Standard Atmosphere Model (ISA):
        - Troposphere (h < 11,000 m): T = T0 - L*h
        - Stratosphere (11,000 m < h < 20,000 m): T = constant
        - Speed of sound: a = sqrt(gamma * R * T)
        """
        import math

        # Constants
        T0 = 288.15  # Sea level standard temperature (K)
        L = 0.0065   # Temperature lapse rate (K/m) in troposphere
        gamma = 1.4  # Ratio of specific heats for air
        R = 287.05   # Specific gas constant for air (J/(kg·K))
        T_strat = 216.65  # Stratosphere temperature (K)
        h_trop = 11000.0  # Tropopause altitude (m)

        # Calculate temperature at altitude
        if altitude < h_trop:
            # Troposphere: temperature decreases linearly with altitude
            temperature = T0 - L * altitude
        else:
            # Stratosphere: temperature is constant
            temperature = T_strat

        # Calculate speed of sound at this temperature
        # a = sqrt(gamma * R * T)
        speed_of_sound = math.sqrt(gamma * R * temperature)

        # Calculate true airspeed
        # V = M * a
        true_airspeed = mach_number * speed_of_sound

        return true_airspeed

    def _get_friendly_method_name(self, method: str) -> str:
        """
        Convert internal method name to user-friendly display name.

        Args:
            method: Internal method name (e.g., 'piston_theory_adaptive')

        Returns:
            User-friendly display name (e.g., 'Piston Theory (Adaptive)')
        """
        method_names = {
            'piston_theory_adaptive': 'Piston Theory (Adaptive)',
            'piston_theory': 'Piston Theory',
            'doublet_lattice': 'Doublet Lattice Method (DLM)',
            'dlm': 'Doublet Lattice Method',
            'nastran_sol145': 'NASTRAN SOL145',
            'pk_method': 'PK Flutter Method',
            'k_method': 'K Flutter Method'
        }
        return method_names.get(method.lower(), method)

    def refresh(self):
        """Refresh the panel."""
        if self.analysis_results:
            self._switch_tab(self.current_view)

    def on_show(self):
        """Called when panel is shown."""
        self.refresh()
