"""Aerodynamic model configuration panel for the GUI."""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any, List
import numpy as np

from models.aerodynamic import (
    AerodynamicModel, FlowConditions, PistonTheoryParameters,
    DoubletLatticeParameters, AerodynamicTheory, FlowType
)
from .base_panel import BasePanel


class AerodynamicsPanel(BasePanel):
    """Panel for aerodynamic model configuration."""

    def __init__(self, parent, main_window):
        self.current_model: Optional[AerodynamicModel] = None
        super().__init__(parent, main_window)
        self._load_current_model()

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Create main content area
        content_frame = self.theme_manager.create_styled_frame(self.frame, elevated=True)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            content_frame,
            text="Aerodynamic Model Configuration",
            style="heading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Create notebook for different sections
        self.notebook = ctk.CTkTabview(content_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.flow_tab = self.notebook.add("Flow Conditions")
        self.theory_tab = self.notebook.add("Aerodynamic Theory")
        self.mesh_tab = self.notebook.add("Aerodynamic Mesh")
        self.spline_tab = self.notebook.add("Spline Connection")
        self.preview_tab = self.notebook.add("Preview")

        self._setup_flow_tab()
        self._setup_theory_tab()
        self._setup_mesh_tab()
        self._setup_spline_tab()
        self._setup_preview_tab()

        # Control buttons
        self._setup_control_buttons(content_frame)

        # Initialize temperature from default altitude (after all UI setup)
        self._update_temperature_from_altitude()

    def _setup_flow_tab(self):
        """Setup flow conditions tab."""
        self.flow_tab.grid_columnconfigure(1, weight=1)

        # Flow conditions section
        flow_frame = self.theme_manager.create_styled_frame(self.flow_tab, elevated=True)
        flow_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        flow_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            flow_frame,
            text="Flow Conditions",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Mach number
        mach_label = self.theme_manager.create_styled_label(flow_frame, text="Mach Number:")
        mach_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.mach_var = ctk.StringVar(value="2.0")
        self.mach_entry = self.theme_manager.create_styled_entry(
            flow_frame,
            textvariable=self.mach_var,
            placeholder_text="Mach number (e.g., 2.0)"
        )
        self.mach_entry.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # REMOVED: Dynamic pressure input - calculated automatically from Mach and altitude

        # Altitude
        alt_label = self.theme_manager.create_styled_label(flow_frame, text="Altitude [m]:")
        alt_label.grid(row=3, column=0, sticky="w", padx=(20, 10), pady=5)

        self.alt_var = ctk.StringVar(value="0")
        self.alt_entry = self.theme_manager.create_styled_entry(
            flow_frame,
            textvariable=self.alt_var,
            placeholder_text="Flight altitude in meters"
        )
        self.alt_entry.grid(row=3, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Temperature (calculated from altitude - display only)
        temp_label = self.theme_manager.create_styled_label(flow_frame, text="Temperature [K]:")
        temp_label.grid(row=4, column=0, sticky="w", padx=(20, 10), pady=5)

        self.temp_var = ctk.StringVar(value="288.15")
        self.temp_display = self.theme_manager.create_styled_label(
            flow_frame,
            text="288.15 (ISA Standard)",
            style="caption"
        )
        self.temp_display.grid(row=4, column=1, sticky="w", padx=(0, 20), pady=5)

        # Flow properties display
        props_frame = self.theme_manager.create_styled_frame(self.flow_tab, elevated=True)
        props_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        props_title = self.theme_manager.create_styled_label(
            props_frame,
            text="Calculated Properties",
            style="subheading"
        )
        props_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.flow_type_label = self.theme_manager.create_styled_label(
            props_frame,
            text="Flow Type: -"
        )
        self.flow_type_label.grid(row=1, column=0, sticky="w", padx=20, pady=2)

        self.velocity_label = self.theme_manager.create_styled_label(
            props_frame,
            text="Flow Velocity: -"
        )
        self.velocity_label.grid(row=2, column=0, sticky="w", padx=20, pady=2)

        self.recommended_theory_label = self.theme_manager.create_styled_label(
            props_frame,
            text="Recommended Theory: -"
        )
        self.recommended_theory_label.grid(row=3, column=0, sticky="w", padx=20, pady=(2, 15))

        # Bind events to update calculations
        self.mach_var.trace("w", self._update_flow_calculations)
        self.alt_var.trace("w", self._update_temperature_from_altitude)

    def _setup_theory_tab(self):
        """Setup aerodynamic theory tab."""
        self.theory_tab.grid_columnconfigure(0, weight=1)

        # Theory selection
        theory_frame = self.theme_manager.create_styled_frame(self.theory_tab, elevated=True)
        theory_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        theory_frame.grid_columnconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            theory_frame,
            text="Aerodynamic Theory Selection",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Theory type
        theory_type_label = self.theme_manager.create_styled_label(theory_frame, text="Theory:")
        theory_type_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.theory_var = ctk.StringVar(value="DOUBLET_LATTICE")
        theory_options = ["PISTON_THEORY", "DOUBLET_LATTICE", "ZAERO"]
        self.theory_combo = ctk.CTkComboBox(
            theory_frame,
            variable=self.theory_var,
            values=theory_options,
            state="readonly",
            command=self._on_theory_changed
        )
        self.theory_combo.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Theory description
        self.theory_description = self.theme_manager.create_styled_label(
            theory_frame,
            text=self._get_theory_description("DOUBLET_LATTICE"),
            style="caption",
            wraplength=500
        )
        self.theory_description.grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 15))

        # Piston theory parameters
        self.piston_frame = self.theme_manager.create_styled_frame(self.theory_tab, elevated=True)
        self.piston_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.piston_frame.grid_columnconfigure(1, weight=1)

        piston_title = self.theme_manager.create_styled_label(
            self.piston_frame,
            text="Piston Theory Parameters",
            style="subheading"
        )
        piston_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Gamma (specific heat ratio)
        gamma_label = self.theme_manager.create_styled_label(self.piston_frame, text="Specific Heat Ratio (γ):")
        gamma_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.gamma_var = ctk.StringVar(value="1.4")
        self.gamma_entry = self.theme_manager.create_styled_entry(
            self.piston_frame,
            textvariable=self.gamma_var,
            placeholder_text="Specific heat ratio (1.4 for air)"
        )
        self.gamma_entry.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Piston theory order
        order_label = self.theme_manager.create_styled_label(self.piston_frame, text="Theory Order:")
        order_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=5)

        self.order_var = ctk.StringVar(value="1")
        order_combo = ctk.CTkComboBox(
            self.piston_frame,
            variable=self.order_var,
            values=["1", "2"],
            state="readonly"
        )
        order_combo.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=(5, 15))

        # Doublet lattice parameters
        self.doublet_frame = self.theme_manager.create_styled_frame(self.theory_tab, elevated=True)
        self.doublet_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.doublet_frame.grid_columnconfigure(1, weight=1)

        doublet_title = self.theme_manager.create_styled_label(
            self.doublet_frame,
            text="Doublet Lattice Parameters",
            style="subheading"
        )
        doublet_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Reduced frequency
        freq_label = self.theme_manager.create_styled_label(self.doublet_frame, text="Reduced Frequency (k):")
        freq_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.freq_var = ctk.StringVar(value="0.0")
        self.freq_entry = self.theme_manager.create_styled_entry(
            self.doublet_frame,
            textvariable=self.freq_var,
            placeholder_text="k = ωb/V (0.0 for steady analysis)"
        )
        self.freq_entry.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(5, 15))

        self._update_theory_visibility()

    def _setup_mesh_tab(self):
        """Setup aerodynamic mesh tab."""
        self.mesh_tab.grid_columnconfigure(1, weight=1)

        # Mesh parameters
        mesh_frame = self.theme_manager.create_styled_frame(self.mesh_tab, elevated=True)
        mesh_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        mesh_frame.grid_columnconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            mesh_frame,
            text="STREAMLINED: Aerodynamic Mesh Uses Structural Mesh",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        info_label = self.theme_manager.create_styled_label(
            mesh_frame,
            text="Aerodynamic mesh is automatically generated from structural mesh.\nSeparate aero mesh parameters removed for simplicity.",
            style="body"
        )
        info_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 15))

        # Number of boxes in X (chordwise)
        nx_aero_label = self.theme_manager.create_styled_label(mesh_frame, text="Chordwise Boxes:")
        nx_aero_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=5)

        self.nx_aero_var = ctk.StringVar(value="4")
        self.nx_aero_entry = self.theme_manager.create_styled_entry(
            mesh_frame,
            textvariable=self.nx_aero_var,
            placeholder_text="Number of aerodynamic boxes in chord direction"
        )
        self.nx_aero_entry.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Number of boxes in Y (spanwise)
        ny_aero_label = self.theme_manager.create_styled_label(mesh_frame, text="Spanwise Boxes:")
        ny_aero_label.grid(row=3, column=0, sticky="w", padx=(20, 10), pady=5)

        self.ny_aero_var = ctk.StringVar(value="2")
        self.ny_aero_entry = self.theme_manager.create_styled_entry(
            mesh_frame,
            textvariable=self.ny_aero_var,
            placeholder_text="Number of aerodynamic boxes in span direction"
        )
        self.ny_aero_entry.grid(row=3, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Z-offset for aerodynamic mesh
        z_offset_label = self.theme_manager.create_styled_label(mesh_frame, text="Z-Offset [m]:")
        z_offset_label.grid(row=4, column=0, sticky="w", padx=(20, 10), pady=5)

        self.z_offset_var = ctk.StringVar(value="0.0")
        self.z_offset_entry = self.theme_manager.create_styled_entry(
            mesh_frame,
            textvariable=self.z_offset_var,
            placeholder_text="Z-offset from structural mesh"
        )
        self.z_offset_entry.grid(row=4, column=1, sticky="ew", padx=(0, 20), pady=(5, 15))

        # Mesh statistics
        stats_frame = self.theme_manager.create_styled_frame(self.mesh_tab, elevated=True)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        stats_title = self.theme_manager.create_styled_label(
            stats_frame,
            text="Mesh Statistics",
            style="subheading"
        )
        stats_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.total_aero_boxes_label = self.theme_manager.create_styled_label(
            stats_frame,
            text="Total Aerodynamic Boxes: -"
        )
        self.total_aero_boxes_label.grid(row=1, column=0, sticky="w", padx=20, pady=2)

        self.aero_element_type_label = self.theme_manager.create_styled_label(
            stats_frame,
            text="Element Type: -"
        )
        self.aero_element_type_label.grid(row=2, column=0, sticky="w", padx=20, pady=(2, 15))

        # Bind events to update calculations
        self.nx_aero_var.trace("w", self._update_mesh_calculations)
        self.ny_aero_var.trace("w", self._update_mesh_calculations)

    def _setup_spline_tab(self):
        """Setup spline connection tab."""
        self.spline_tab.grid_columnconfigure(0, weight=1)

        # Spline information
        spline_frame = self.theme_manager.create_styled_frame(self.spline_tab, elevated=True)
        spline_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        title_label = self.theme_manager.create_styled_label(
            spline_frame,
            text="Structural-Aerodynamic Spline Connection",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        info_text = ("The spline connection interpolates forces and displacements between "
                    "the structural and aerodynamic models. This connection is automatically "
                    "generated based on the structural mesh.")

        info_label = self.theme_manager.create_styled_label(
            spline_frame,
            text=info_text,
            style="caption",
            wraplength=500
        )
        info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(5, 15))

        # Spline statistics
        self.spline_points_label = self.theme_manager.create_styled_label(
            spline_frame,
            text="Spline Points: -"
        )
        self.spline_points_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 15))

    def _setup_preview_tab(self):
        """Setup model preview tab."""
        self.preview_tab.grid_columnconfigure(0, weight=1)
        self.preview_tab.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            self.preview_tab,
            text="Aerodynamic Model Preview",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Preview text area
        self.preview_text = ctk.CTkTextbox(
            self.preview_tab,
            wrap="none",
            font=("Courier", 11)
        )
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_control_buttons(self, parent):
        """Setup control buttons."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Generate mesh button
        self.generate_button = self.theme_manager.create_styled_button(
            button_frame,
            text="Generate Aerodynamic Mesh",
            style="primary",
            command=self._generate_aero_mesh
        )
        self.generate_button.pack(side="left", padx=(0, 10))

        # Validate button
        self.validate_button = self.theme_manager.create_styled_button(
            button_frame,
            text="Validate Model",
            style="secondary",
            command=self._validate_model
        )
        self.validate_button.pack(side="left", padx=(0, 10))

        # Save button
        self.save_button = self.theme_manager.create_styled_button(
            button_frame,
            text="Save Model",
            style="success",
            command=self._save_model
        )
        self.save_button.pack(side="left")

    def _load_current_model(self):
        """Load the current aerodynamic model if it exists."""
        if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
            if not hasattr(self.project_manager.current_project, 'aerodynamic_model'):
                self.current_model = AerodynamicModel(1, "Aerodynamic Model")
                self.project_manager.current_project.aerodynamic_model = self.current_model
            else:
                self.current_model = self.project_manager.current_project.aerodynamic_model
        else:
            self.current_model = AerodynamicModel(1, "Aerodynamic Model")

    def _calculate_isa_temperature(self, altitude: float) -> float:
        """Calculate ISA (International Standard Atmosphere) temperature from altitude.

        Args:
            altitude: Altitude in meters

        Returns:
            Temperature in Kelvin
        """
        if altitude < 11000:
            # Troposphere: Linear temperature decrease
            return 288.15 - 0.0065 * altitude
        else:
            # Stratosphere: Constant temperature
            return 216.65

    def _update_temperature_from_altitude(self, *args):
        """Update temperature when altitude changes (ISA model)."""
        # Skip if UI not yet initialized
        if not hasattr(self, 'temp_display'):
            return

        try:
            alt = float(self.alt_var.get())
            temp = self._calculate_isa_temperature(alt)
            self.temp_var.set(f"{temp:.2f}")
            self.temp_display.configure(text=f"{temp:.2f} K (ISA)")
            self._update_flow_calculations()
        except ValueError:
            self.temp_var.set("288.15")
            self.temp_display.configure(text="288.15 K (ISA)")

    def _update_flow_calculations(self, *args):
        """Update flow calculations when inputs change."""
        try:
            mach = float(self.mach_var.get())
            temp = float(self.temp_var.get())

            if mach > 0 and temp > 0:
                # Calculate flow properties
                if mach < 0.8:
                    flow_type = "SUBSONIC"
                elif mach < 1.2:
                    flow_type = "TRANSONIC"
                elif mach < 5.0:
                    flow_type = "SUPERSONIC"
                else:
                    flow_type = "HYPERSONIC"

                # Calculate velocity
                gamma = 1.4
                R = 287.0
                speed_of_sound = np.sqrt(gamma * R * temp)
                velocity = mach * speed_of_sound

                # Recommended theory
                if mach < 0.6:
                    recommended = "Doublet Lattice Method"
                elif mach > 1.2:
                    recommended = "Piston Theory"
                else:
                    recommended = "Either (Piston Theory preferred)"

                self.flow_type_label.configure(text=f"Flow Type: {flow_type}")
                self.velocity_label.configure(text=f"Flow Velocity: {velocity:.1f} m/s")
                self.recommended_theory_label.configure(text=f"Recommended Theory: {recommended}")
            else:
                self.flow_type_label.configure(text="Flow Type: -")
                self.velocity_label.configure(text="Flow Velocity: -")
                self.recommended_theory_label.configure(text="Recommended Theory: -")
        except ValueError:
            self.flow_type_label.configure(text="Flow Type: -")
            self.velocity_label.configure(text="Flow Velocity: -")
            self.recommended_theory_label.configure(text="Recommended Theory: -")

        self._update_mesh_calculations()

    def _update_mesh_calculations(self, *args):
        """Update mesh calculations when inputs change."""
        # Skip if mesh variables not yet initialized
        if not hasattr(self, 'nx_aero_var') or not hasattr(self, 'ny_aero_var'):
            return

        try:
            nx_aero = int(self.nx_aero_var.get())
            ny_aero = int(self.ny_aero_var.get())

            if nx_aero > 0 and ny_aero > 0:
                total_boxes = nx_aero * ny_aero
                theory = self.theory_var.get()
                element_type = "CAERO5" if theory == "PISTON_THEORY" else "CAERO1"

                self.total_aero_boxes_label.configure(text=f"Total Aerodynamic Boxes: {total_boxes}")
                self.aero_element_type_label.configure(text=f"Element Type: {element_type}")
            else:
                self.total_aero_boxes_label.configure(text="Total Aerodynamic Boxes: -")
                self.aero_element_type_label.configure(text="Element Type: -")
        except ValueError:
            self.total_aero_boxes_label.configure(text="Total Aerodynamic Boxes: -")
            self.aero_element_type_label.configure(text="Element Type: -")

    def _on_theory_changed(self, *args):
        """Handle theory selection change."""
        self._update_theory_visibility()
        self._update_mesh_calculations()
        theory = self.theory_var.get()
        description = self._get_theory_description(theory)
        self.theory_description.configure(text=description)

    def _update_theory_visibility(self):
        """Update visibility of theory-specific parameters."""
        theory = self.theory_var.get()

        if theory == "PISTON_THEORY":
            self.piston_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
            self.doublet_frame.grid_remove()
        elif theory == "DOUBLET_LATTICE":
            self.doublet_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
            self.piston_frame.grid_remove()
        else:  # ZAERO
            self.piston_frame.grid_remove()
            self.doublet_frame.grid_remove()

    def _get_theory_description(self, theory: str) -> str:
        """Get description for aerodynamic theory."""
        descriptions = {
            "PISTON_THEORY": "Piston Theory (CAERO5): Suitable for supersonic and hypersonic flows (M > 1.2). Computationally efficient for high Mach number flutter analysis.",
            "DOUBLET_LATTICE": "Doublet Lattice Method (CAERO1): Best for subsonic flows (M < 0.8). Uses potential flow theory for accurate low-speed flutter analysis.",
            "ZAERO": "ZAERO Advanced Aerodynamics: High-fidelity aerodynamic modeling for all Mach number ranges. Requires ZAERO license."
        }
        return descriptions.get(theory, "Advanced aerodynamic method")

    def _generate_aero_mesh(self):
        """Generate the aerodynamic mesh."""
        try:
            # Get structural model dimensions
            if not hasattr(self.project_manager.current_project, 'structural_model'):
                messagebox.showerror("Error", "No structural model found. Create structural model first.")
                return

            structural_model = self.project_manager.current_project.structural_model
            if not structural_model.geometry:
                messagebox.showerror("Error", "Structural geometry not defined. Complete structural model first.")
                return

            # Create flow conditions
            mach = float(self.mach_var.get())
            alt = float(self.alt_var.get())
            temp = float(self.temp_var.get())

            # Calculate dynamic pressure from atmospheric conditions
            # Standard atmosphere approximation
            if alt == 0:
                density = 1.225  # kg/m³ at sea level
                pressure = 101325  # Pa at sea level
            else:
                # Simple altitude correction (more accurate would use ISA model)
                density = 1.225 * (1 - 0.0065 * alt / 288.15)**4.256
                pressure = 101325 * (1 - 0.0065 * alt / 288.15)**5.256

            # Calculate velocity from Mach number: V = M * sqrt(gamma * R * T)
            gamma = 1.4  # specific heat ratio for air
            R = 287.0  # specific gas constant for air (J/kg·K)
            velocity = mach * (gamma * R * temp)**0.5

            # Calculate dynamic pressure: q = 0.5 * rho * V²
            q = 0.5 * density * velocity**2

            flow_conditions = FlowConditions(mach, q, alt, temp, pressure, density)
            self.current_model.set_flow_conditions(flow_conditions)

            # Set theory parameters
            theory = AerodynamicTheory(self.theory_var.get())
            self.current_model.theory = theory

            if theory == AerodynamicTheory.PISTON_THEORY:
                gamma = float(self.gamma_var.get())
                order = int(self.order_var.get())
                piston_params = PistonTheoryParameters(gamma, 0.0, order)
                self.current_model.set_piston_theory_parameters(piston_params)
            elif theory == AerodynamicTheory.DOUBLET_LATTICE:
                freq = float(self.freq_var.get())
                doublet_params = DoubletLatticeParameters(freq)
                self.current_model.set_doublet_lattice_parameters(doublet_params)

            # Generate aerodynamic mesh
            nx_aero = int(self.nx_aero_var.get())
            ny_aero = int(self.ny_aero_var.get())
            z_offset = float(self.z_offset_var.get())

            panel_length = structural_model.geometry.length
            panel_width = structural_model.geometry.width

            success = self.current_model.generate_aerodynamic_mesh(
                panel_length, panel_width, nx_aero, ny_aero, z_offset
            )

            if success:
                # Create spline connection
                if structural_model.nodes:
                    spline_points = [(node.node_id, node.x, node.y, node.z)
                                   for node in structural_model.nodes]
                    self.current_model.create_spline_connection(spline_points)

                self._update_preview()
                self._update_spline_info()
                messagebox.showinfo("Success", "Aerodynamic mesh generated successfully!")
                self.logger.info(f"Generated aerodynamic mesh with {len(self.current_model.elements)} elements")
            else:
                messagebox.showerror("Error", "Failed to generate aerodynamic mesh")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error generating aerodynamic mesh: {str(e)}")
            self.logger.error(f"Error generating aerodynamic mesh: {str(e)}")

    def _validate_model(self):
        """Validate the current aerodynamic model."""
        if not self.current_model:
            messagebox.showwarning("Warning", "No model to validate")
            return

        is_valid, errors = self.current_model.validate()

        if is_valid:
            messagebox.showinfo("Validation", "Aerodynamic model is valid!")
        else:
            error_message = "Model validation failed:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Validation Failed", error_message)

    def _calculate_default_velocities(self, flow_conditions, project):
        """Calculate default velocity sweep based on flutter speed estimate."""
        import numpy as np

        try:
            # Get panel properties
            if not hasattr(project, 'geometry') or not project.geometry:
                return None

            geom = project.geometry
            mat = project.material

            if not mat:
                return None

            # Extract parameters
            L = geom.get('length', 0.5)  # m
            h = geom.get('thickness', 0.003)  # m
            E = getattr(mat, 'youngs_modulus', 70e9)  # Pa
            rho_mat = getattr(mat, 'density', 2700)  # kg/m³

            mach = flow_conditions.mach_number
            temp = getattr(flow_conditions, 'temperature', 288.15)
            rho_air = getattr(flow_conditions, 'density', 1.225)

            # Estimate flutter speed using simplified formula
            m = rho_mat * h  # Mass per area
            mu = m / (rho_air * L)  # Mass ratio

            # First mode frequency estimate
            nu = 0.33
            D = E * h**3 / (12 * (1 - nu**2))
            omega = np.sqrt(D / m) * ((np.pi / L)**2 + (np.pi / L)**2)
            f_1 = omega / (2 * np.pi)

            # Flutter speed estimate
            a = np.sqrt(1.4 * 287 * temp)  # Speed of sound
            if mach > 1.0:
                # Supersonic estimate
                q_f = D / L**3 * 10
                V_f = np.sqrt(2 * q_f / rho_air)
            else:
                # Subsonic estimate
                V_f = f_1 * L * np.sqrt(mu) * 3.0

            # Create velocity sweep: 0.3*V_f to 3*V_f with fine spacing near V_f
            v_min = max(50, V_f * 0.3)
            v_max = V_f * 3.0

            # Generate points with finer resolution near V_f
            velocities = []
            velocities.extend(np.linspace(v_min, V_f * 0.8, 3).tolist())
            velocities.extend(np.linspace(V_f * 0.8, V_f * 1.2, 5).tolist())
            velocities.extend(np.linspace(V_f * 1.2, v_max, 4).tolist())

            # Remove duplicates and sort
            velocities = sorted(list(set([round(v, 1) for v in velocities])))

            self.logger.info(f"Calculated default velocities: {len(velocities)} points from {v_min:.0f} to {v_max:.0f} m/s")
            self.logger.info(f"Estimated flutter speed: {V_f:.1f} m/s")

            return velocities

        except Exception as e:
            self.logger.warning(f"Could not calculate default velocities: {e}")
            return None

    def _save_model(self):
        """Save the current aerodynamic model."""
        if not self.current_model:
            messagebox.showwarning("Warning", "No model to save")
            return

        try:
            if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
                project = self.project_manager.current_project

                # Save to both aerodynamic_model AND aerodynamic_config for compatibility
                project.aerodynamic_model = self.current_model

                # Also save as aerodynamic_config (dict format) for analysis panel
                if self.current_model.flow_conditions:
                    fc = self.current_model.flow_conditions

                    # Calculate default velocity sweep
                    velocities = self._calculate_default_velocities(fc, project)

                    aerodynamic_config = {
                        'flow_conditions': {
                            'mach_number': fc.mach_number,
                            'altitude': fc.altitude,
                            'temperature': getattr(fc, 'temperature', None),
                            'pressure': getattr(fc, 'pressure', None),
                            'density': getattr(fc, 'density', None)
                        },
                        'theory': self.current_model.theory.value if hasattr(self.current_model.theory, 'value') else str(self.current_model.theory)
                    }

                    # Add velocities if calculated
                    if velocities:
                        aerodynamic_config['velocities'] = velocities
                        self.logger.info(f"Saved {len(velocities)} velocity points to config")

                    project.aerodynamic_config = aerodynamic_config
                    self.logger.info(f"Saved aerodynamic config: M={fc.mach_number}")

                self.project_manager.save_current_project()
                messagebox.showinfo("Success", "Aerodynamic model saved successfully!")
                self.logger.info("Aerodynamic model saved to project")
            else:
                messagebox.showwarning("Warning", "No active project to save to")

        except Exception as e:
            messagebox.showerror("Error", f"Error saving model: {str(e)}")
            self.logger.error(f"Error saving aerodynamic model: {str(e)}")

    def _update_spline_info(self):
        """Update spline connection information."""
        if self.current_model and self.current_model.spline_points:
            count = len(self.current_model.spline_points)
            self.spline_points_label.configure(text=f"Spline Points: {count}")
        else:
            self.spline_points_label.configure(text="Spline Points: -")

    def _update_preview(self):
        """Update the model preview."""
        if not self.current_model:
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", "No aerodynamic model created yet.")
            return

        # Generate preview text
        info = self.current_model.get_model_info()

        preview_text = f"""NASTRAN Panel Flutter Aerodynamic Model
{'=' * 50}

Model Information:
  Name: {info['name']}
  Model ID: {info['model_id']}
  Theory: {info['theory']}

Flow Conditions:
"""

        if info['flow_conditions']:
            fc = info['flow_conditions']
            preview_text += f"""  Mach Number: {fc['mach_number']:.2f}
  Dynamic Pressure: {fc['dynamic_pressure']:.0f} Pa
  Flow Type: {fc['flow_type']}
  Flow Velocity: {fc['flow_velocity']:.1f} m/s
  Altitude: {fc['altitude']:.0f} m
  Temperature: {fc['temperature']:.2f} K
"""
        else:
            preview_text += "  Not defined\n"

        preview_text += "\nAerodynamic Mesh:\n"

        if info['mesh']:
            mesh = info['mesh']
            preview_text += f"""  Chordwise Boxes: {mesh['nx_aero']}
  Spanwise Boxes: {mesh['ny_aero']}
  Total Boxes: {mesh['total_boxes']}
"""
        else:
            preview_text += "  Not generated\n"

        preview_text += f"""
Statistics:
  Elements: {info['elements_count']}
  Spline Points: {info['spline_points_count']}

Mesh Generated: {'✓ YES' if info['mesh_generated'] else '✗ NO'}
"""

        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", preview_text)

    def _load_aerodynamic_config_from_project(self):
        """Load aerodynamic config data from project and populate GUI fields."""
        if not hasattr(self.project_manager, 'current_project') or not self.project_manager.current_project:
            return

        project = self.project_manager.current_project

        # Load aerodynamic config if it exists
        if project.aerodynamic_config:
            try:
                flow_conditions = project.aerodynamic_config.get('flow_conditions', {})

                # Load flow conditions
                if 'mach_number' in flow_conditions:
                    self.mach_var.set(str(flow_conditions['mach_number']))
                if 'altitude' in flow_conditions:
                    self.alt_var.set(str(flow_conditions['altitude']))
                # Temperature is auto-calculated from altitude, no need to load it
                # Update display after altitude is loaded
                if 'altitude' in flow_conditions:
                    self._update_temperature_from_altitude()

                self.logger.info("Loaded aerodynamic config from project")
            except Exception as e:
                self.logger.warning(f"Error loading aerodynamic config from project: {e}")

    def refresh(self):
        """Refresh panel with current project data."""
        self._load_current_model()
        self._load_aerodynamic_config_from_project()  # Load saved data into GUI fields
        self._update_flow_calculations()
        self._update_mesh_calculations()
        self._update_spline_info()
        self._update_preview()

    def on_show(self):
        """Called when panel is shown."""
        self.refresh()