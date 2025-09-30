"""Structural model generation panel for the GUI."""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any, List
import numpy as np

from models.structural import (
    StructuralModel, PanelGeometry, MeshParameters, StructuralProperties,
    BoundaryCondition, ElementType
)
from models.material import IsotropicMaterial, OrthotropicMaterial, PredefinedMaterials
from .base_panel import BasePanel


class StructuralPanel(BasePanel):
    """Panel for structural model generation and configuration."""

    def __init__(self, parent, main_window):
        self.current_model: Optional[StructuralModel] = None
        super().__init__(parent, main_window)
        self._load_current_model()

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Create main content area
        content_frame = self.theme_manager.create_styled_frame(self.frame, elevated=True)
        content_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            content_frame,
            text="Structural Model Generation",
            style="heading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Create notebook for different sections
        self.notebook = ctk.CTkTabview(content_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.geometry_tab = self.notebook.add("Geometry")
        self.mesh_tab = self.notebook.add("Mesh")
        self.properties_tab = self.notebook.add("Properties")
        self.boundary_tab = self.notebook.add("Boundary Conditions")
        self.preview_tab = self.notebook.add("Preview")

        self._setup_geometry_tab()
        self._setup_mesh_tab()
        self._setup_properties_tab()
        self._setup_boundary_tab()
        self._setup_preview_tab()

        # Control buttons
        self._setup_control_buttons(content_frame)

    def _setup_geometry_tab(self):
        """Setup geometry configuration tab."""
        self.geometry_tab.grid_columnconfigure(1, weight=1)

        # Panel dimensions section
        dimensions_frame = self.theme_manager.create_styled_frame(self.geometry_tab, elevated=True)
        dimensions_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        dimensions_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            dimensions_frame,
            text="Panel Dimensions",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Length
        length_label = self.theme_manager.create_styled_label(dimensions_frame, text="Length (a) [m]:")
        length_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.length_var = ctk.StringVar(value="1.0")
        self.length_entry = self.theme_manager.create_styled_entry(
            dimensions_frame,
            textvariable=self.length_var,
            placeholder_text="Panel length in meters"
        )
        self.length_entry.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Width
        width_label = self.theme_manager.create_styled_label(dimensions_frame, text="Width (b) [m]:")
        width_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=5)

        self.width_var = ctk.StringVar(value="0.5")
        self.width_entry = self.theme_manager.create_styled_entry(
            dimensions_frame,
            textvariable=self.width_var,
            placeholder_text="Panel width in meters"
        )
        self.width_entry.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Thickness
        thickness_label = self.theme_manager.create_styled_label(dimensions_frame, text="Thickness [m]:")
        thickness_label.grid(row=3, column=0, sticky="w", padx=(20, 10), pady=5)

        self.thickness_var = ctk.StringVar(value="0.002")
        self.thickness_entry = self.theme_manager.create_styled_entry(
            dimensions_frame,
            textvariable=self.thickness_var,
            placeholder_text="Panel thickness in meters"
        )
        self.thickness_entry.grid(row=3, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Calculated properties
        calc_frame = self.theme_manager.create_styled_frame(self.geometry_tab, elevated=True)
        calc_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        calc_title = self.theme_manager.create_styled_label(
            calc_frame,
            text="Calculated Properties",
            style="subheading"
        )
        calc_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.aspect_ratio_label = self.theme_manager.create_styled_label(
            calc_frame,
            text="Aspect Ratio: -"
        )
        self.aspect_ratio_label.grid(row=1, column=0, sticky="w", padx=20, pady=2)

        self.area_label = self.theme_manager.create_styled_label(
            calc_frame,
            text="Area: -"
        )
        self.area_label.grid(row=2, column=0, sticky="w", padx=20, pady=(2, 15))

        # Bind events to update calculations
        self.length_var.trace("w", self._update_geometry_calculations)
        self.width_var.trace("w", self._update_geometry_calculations)

    def _setup_mesh_tab(self):
        """Setup mesh configuration tab."""
        self.mesh_tab.grid_columnconfigure(1, weight=1)

        # Mesh parameters
        mesh_frame = self.theme_manager.create_styled_frame(self.mesh_tab, elevated=True)
        mesh_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        mesh_frame.grid_columnconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            mesh_frame,
            text="Mesh Parameters",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Number of elements in X
        nx_label = self.theme_manager.create_styled_label(mesh_frame, text="Elements in X:")
        nx_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.nx_var = ctk.StringVar(value="20")
        self.nx_entry = self.theme_manager.create_styled_entry(
            mesh_frame,
            textvariable=self.nx_var,
            placeholder_text="Number of elements in length direction"
        )
        self.nx_entry.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Number of elements in Y
        ny_label = self.theme_manager.create_styled_label(mesh_frame, text="Elements in Y:")
        ny_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=5)

        self.ny_var = ctk.StringVar(value="10")
        self.ny_entry = self.theme_manager.create_styled_entry(
            mesh_frame,
            textvariable=self.ny_var,
            placeholder_text="Number of elements in width direction"
        )
        self.ny_entry.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Element type
        element_type_label = self.theme_manager.create_styled_label(mesh_frame, text="Element Type:")
        element_type_label.grid(row=3, column=0, sticky="w", padx=(20, 10), pady=5)

        self.element_type_var = ctk.StringVar(value="CQUAD4")
        self.element_type_combo = ctk.CTkComboBox(
            mesh_frame,
            variable=self.element_type_var,
            values=["CQUAD4", "CQUAD8", "CTRIA3", "CTRIA6"],
            state="readonly"
        )
        self.element_type_combo.grid(row=3, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Mesh statistics
        stats_frame = self.theme_manager.create_styled_frame(self.mesh_tab, elevated=True)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        stats_title = self.theme_manager.create_styled_label(
            stats_frame,
            text="Mesh Statistics",
            style="subheading"
        )
        stats_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.total_elements_label = self.theme_manager.create_styled_label(
            stats_frame,
            text="Total Elements: -"
        )
        self.total_elements_label.grid(row=1, column=0, sticky="w", padx=20, pady=2)

        self.total_nodes_label = self.theme_manager.create_styled_label(
            stats_frame,
            text="Total Nodes: -"
        )
        self.total_nodes_label.grid(row=2, column=0, sticky="w", padx=20, pady=2)

        self.element_size_label = self.theme_manager.create_styled_label(
            stats_frame,
            text="Element Size: -"
        )
        self.element_size_label.grid(row=3, column=0, sticky="w", padx=20, pady=(2, 15))

        # Bind events to update calculations
        self.nx_var.trace("w", self._update_mesh_calculations)
        self.ny_var.trace("w", self._update_mesh_calculations)
        self.element_type_var.trace("w", self._update_mesh_calculations)

    def _setup_properties_tab(self):
        """Setup properties configuration tab."""
        self.properties_tab.grid_columnconfigure(0, weight=1)

        # Material selection
        material_frame = self.theme_manager.create_styled_frame(self.properties_tab, elevated=True)
        material_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        material_frame.grid_columnconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            material_frame,
            text="Material Assignment",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Material selection combo
        material_label = self.theme_manager.create_styled_label(material_frame, text="Material:")
        material_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.material_var = ctk.StringVar(value="Aluminum 6061-T6")
        material_options = [
            "Aluminum 6061-T6", "Steel AISI 4340", "Titanium Ti-6Al-4V",
            "Carbon Fiber T300/5208", "Custom Material"
        ]
        self.material_combo = ctk.CTkComboBox(
            material_frame,
            variable=self.material_var,
            values=material_options,
            state="readonly"
        )
        self.material_combo.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Property ID
        prop_id_label = self.theme_manager.create_styled_label(material_frame, text="Property ID:")
        prop_id_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=5)

        self.prop_id_var = ctk.StringVar(value="1")
        self.prop_id_entry = self.theme_manager.create_styled_entry(
            material_frame,
            textvariable=self.prop_id_var,
            placeholder_text="Property ID number"
        )
        self.prop_id_entry.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=(5, 15))

    def _setup_boundary_tab(self):
        """Setup boundary conditions tab."""
        self.boundary_tab.grid_columnconfigure(0, weight=1)

        # Boundary condition selection
        bc_frame = self.theme_manager.create_styled_frame(self.boundary_tab, elevated=True)
        bc_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        bc_frame.grid_columnconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            bc_frame,
            text="Boundary Conditions",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Boundary condition type
        bc_type_label = self.theme_manager.create_styled_label(bc_frame, text="Type:")
        bc_type_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.bc_type_var = ctk.StringVar(value="SSSS")
        bc_options = ["SSSS", "CCCC", "CFFF", "CFCF", "SCSC"]
        self.bc_type_combo = ctk.CTkComboBox(
            bc_frame,
            variable=self.bc_type_var,
            values=bc_options,
            state="readonly"
        )
        self.bc_type_combo.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Description
        self.bc_description = self.theme_manager.create_styled_label(
            bc_frame,
            text=self._get_bc_description("SSSS"),
            style="caption",
            wraplength=400
        )
        self.bc_description.grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 15))

        # Bind event to update description
        self.bc_type_var.trace("w", self._update_bc_description)

    def _setup_preview_tab(self):
        """Setup model preview tab."""
        self.preview_tab.grid_columnconfigure(0, weight=1)
        self.preview_tab.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            self.preview_tab,
            text="Model Preview",
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
            text="Generate Mesh",
            style="primary",
            command=self._generate_mesh
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
        """Load the current structural model if it exists."""
        if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
            # Create a new model if none exists
            if not hasattr(self.project_manager.current_project, 'structural_model'):
                self.current_model = StructuralModel(1, "Panel Structure")
                self.project_manager.current_project.structural_model = self.current_model
            else:
                self.current_model = self.project_manager.current_project.structural_model
                # If structural_model is None, create a new one
                if self.current_model is None:
                    self.current_model = StructuralModel(1, "Panel Structure")
                    self.project_manager.current_project.structural_model = self.current_model
        else:
            self.current_model = StructuralModel(1, "Panel Structure")

    def _update_geometry_calculations(self, *args):
        """Update geometry calculations when inputs change."""
        try:
            length = float(self.length_var.get())
            width = float(self.width_var.get())

            if length > 0 and width > 0:
                aspect_ratio = length / width
                area = length * width

                self.aspect_ratio_label.configure(text=f"Aspect Ratio: {aspect_ratio:.2f}")
                self.area_label.configure(text=f"Area: {area:.4f} m²")
            else:
                self.aspect_ratio_label.configure(text="Aspect Ratio: -")
                self.area_label.configure(text="Area: -")
        except ValueError:
            self.aspect_ratio_label.configure(text="Aspect Ratio: -")
            self.area_label.configure(text="Area: -")

        self._update_mesh_calculations()

    def _update_mesh_calculations(self, *args):
        """Update mesh calculations when inputs change."""
        try:
            nx = int(self.nx_var.get())
            ny = int(self.ny_var.get())
            length = float(self.length_var.get())
            width = float(self.width_var.get())

            if nx > 0 and ny > 0:
                total_elements = nx * ny
                element_type = ElementType(self.element_type_var.get())

                if element_type == ElementType.CQUAD4:
                    total_nodes = (nx + 1) * (ny + 1)
                elif element_type == ElementType.CQUAD8:
                    total_nodes = (2 * nx + 1) * (2 * ny + 1)
                else:
                    total_nodes = (nx + 1) * (ny + 1)  # Simplified

                self.total_elements_label.configure(text=f"Total Elements: {total_elements}")
                self.total_nodes_label.configure(text=f"Total Nodes: {total_nodes}")

                if length > 0 and width > 0:
                    dx = length / nx
                    dy = width / ny
                    element_size = min(dx, dy)
                    self.element_size_label.configure(text=f"Element Size: {element_size:.4f} m")
                else:
                    self.element_size_label.configure(text="Element Size: -")
            else:
                self.total_elements_label.configure(text="Total Elements: -")
                self.total_nodes_label.configure(text="Total Nodes: -")
                self.element_size_label.configure(text="Element Size: -")
        except ValueError:
            self.total_elements_label.configure(text="Total Elements: -")
            self.total_nodes_label.configure(text="Total Nodes: -")
            self.element_size_label.configure(text="Element Size: -")

    def _update_bc_description(self, *args):
        """Update boundary condition description."""
        bc_type = self.bc_type_var.get()
        description = self._get_bc_description(bc_type)
        self.bc_description.configure(text=description)

    def _get_bc_description(self, bc_type: str) -> str:
        """Get description for boundary condition type."""
        descriptions = {
            "SSSS": "Simply supported on all four edges (rotation allowed, translation constrained in z-direction)",
            "CCCC": "Clamped on all four edges (all translations and rotations constrained)",
            "CFFF": "Cantilever configuration (clamped at x=0, free on other edges)",
            "CFCF": "Clamped-Free-Clamped-Free (clamped at x=0 and x=L, free at y=0 and y=W)",
            "SCSC": "Simply supported-Clamped alternating pattern"
        }
        return descriptions.get(bc_type, "Custom boundary condition")

    def _generate_mesh(self):
        """Generate the structural mesh."""
        try:
            # Validate inputs
            length = float(self.length_var.get())
            width = float(self.width_var.get())
            thickness = float(self.thickness_var.get())
            nx = int(self.nx_var.get())
            ny = int(self.ny_var.get())

            if length <= 0 or width <= 0 or thickness <= 0:
                messagebox.showerror("Error", "All dimensions must be positive")
                return

            if nx < 1 or ny < 1:
                messagebox.showerror("Error", "Number of elements must be at least 1")
                return

            # Create geometry and mesh parameters
            geometry = PanelGeometry(length, width, thickness)
            element_type = ElementType(self.element_type_var.get())
            mesh_params = MeshParameters(nx, ny, element_type)

            # Create structural properties
            material_name = self.material_var.get()
            prop_id = int(self.prop_id_var.get())
            material_id = 1  # Default material ID

            # Set up the model
            self.current_model.set_geometry(geometry)
            self.current_model.set_mesh_parameters(mesh_params)
            self.current_model.boundary_condition = BoundaryCondition(self.bc_type_var.get())

            # Add structural property
            struct_prop = StructuralProperties(
                property_id=prop_id,
                material_id=material_id,
                membrane_thickness=thickness
            )
            self.current_model.properties = [struct_prop]  # Replace existing

            # Generate the mesh
            success = self.current_model.generate_mesh()

            if success:
                self._update_preview()
                messagebox.showinfo("Success", "Mesh generated successfully!")
                self.logger.info(f"Generated mesh with {len(self.current_model.elements)} elements and {len(self.current_model.nodes)} nodes")
            else:
                messagebox.showerror("Error", "Failed to generate mesh")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error generating mesh: {str(e)}")
            self.logger.error(f"Error generating mesh: {str(e)}")

    def _validate_model(self):
        """Validate the current structural model."""
        if not self.current_model:
            messagebox.showwarning("Warning", "No model to validate")
            return

        is_valid, errors = self.current_model.validate()

        if is_valid:
            messagebox.showinfo("Validation", "Model is valid!")
        else:
            error_message = "Model validation failed:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Validation Failed", error_message)

    def _save_model(self):
        """Save the current structural model."""
        if not self.current_model:
            messagebox.showwarning("Warning", "No model to save")
            return

        try:
            # Save to project manager
            if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
                self.project_manager.current_project.structural_model = self.current_model
                self.project_manager.save_current_project()
                messagebox.showinfo("Success", "Structural model saved successfully!")
                self.logger.info("Structural model saved to project")
            else:
                messagebox.showwarning("Warning", "No active project to save to")

        except Exception as e:
            messagebox.showerror("Error", f"Error saving model: {str(e)}")
            self.logger.error(f"Error saving structural model: {str(e)}")

    def _update_preview(self):
        """Update the model preview."""
        if not self.current_model or not self.current_model._mesh_generated:
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", "No mesh generated yet. Click 'Generate Mesh' to create the structural model.")
            return

        # Generate preview text
        info = self.current_model.get_model_info()

        preview_text = f"""NASTRAN Panel Flutter Structural Model
{'=' * 50}

Model Information:
  Name: {info['name']}
  Model ID: {info['model_id']}

Geometry:
  Length (a): {info['geometry']['length']:.4f} m
  Width (b): {info['geometry']['width']:.4f} m
  Thickness: {info['geometry']['thickness']:.6f} m
  Aspect Ratio: {info['geometry']['aspect_ratio']:.2f}
  Area: {info['geometry']['area']:.6f} m²

Mesh:
  Elements in X: {info['mesh']['nx']}
  Elements in Y: {info['mesh']['ny']}
  Element Type: {info['mesh']['element_type']}
  Total Elements: {info['mesh']['total_elements']}
  Total Nodes: {info['mesh']['total_nodes']}

Boundary Condition: {info['boundary_condition']}

Statistics:
  Properties: {info['properties_count']}
  Nodes: {info['nodes_count']}
  Elements: {info['elements_count']}
  Constraints: {info['constraints_count']}

Validation: {'✓ PASSED' if info['mesh_generated'] else '✗ FAILED'}
"""

        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", preview_text)

    def refresh_panel(self):
        """Refresh the panel with current data."""
        self._load_current_model()
        self._update_geometry_calculations()
        self._update_mesh_calculations()
        self._update_preview()

    def refresh(self):
        """Refresh panel with current project data (BasePanel interface)."""
        self.refresh_panel()

    def on_show(self):
        """Called when panel is shown."""
        self.refresh_panel()