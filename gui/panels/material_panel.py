"""Material definition panel."""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

from .base_panel import BasePanel
from models.material import (
    IsotropicMaterial, OrthotropicMaterial, CompositeLaminate,
    PredefinedMaterials, MaterialType
)

class MaterialPanel(BasePanel):
    """Panel for defining material properties."""

    def _setup_ui(self):
        """Setup the material panel UI."""
        # Main scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.frame,
            corner_radius=0,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = self.create_section_header(self.scroll_frame, "Material Properties")
        header.pack(anchor="w", pady=(0, 20))

        # Material type selection
        self._create_material_type_section()

        # Predefined materials section
        self._create_predefined_section()

        # Custom material section
        self._create_custom_section()

        # Material preview section
        self._create_preview_section()

        # Navigation buttons
        self._create_navigation()

        # Initialize with current material
        self.current_material_type = MaterialType.ISOTROPIC
        self._refresh_material_display()

    def _create_material_type_section(self):
        """Create material type selection section."""
        type_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        type_frame.pack(fill="x", pady=(0, 20))

        header = self.theme_manager.create_styled_label(
            type_frame,
            text="Material Type",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 10))

        # Material type tabs
        self.material_type_var = ctk.StringVar(value="isotropic")

        type_buttons_frame = ctk.CTkFrame(type_frame, fg_color="transparent")
        type_buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.isotropic_btn = ctk.CTkRadioButton(
            type_buttons_frame,
            text="🔧 Isotropic",
            variable=self.material_type_var,
            value="isotropic",
            command=self._on_material_type_changed,
            font=ctk.CTkFont(size=12)
        )
        self.isotropic_btn.pack(side="left", padx=(0, 20))

        self.orthotropic_btn = ctk.CTkRadioButton(
            type_buttons_frame,
            text="📐 Orthotropic",
            variable=self.material_type_var,
            value="orthotropic",
            command=self._on_material_type_changed,
            font=ctk.CTkFont(size=12)
        )
        self.orthotropic_btn.pack(side="left", padx=(0, 20))

        self.composite_btn = ctk.CTkRadioButton(
            type_buttons_frame,
            text="📚 Composite",
            variable=self.material_type_var,
            value="composite",
            command=self._on_material_type_changed,
            font=ctk.CTkFont(size=12)
        )
        self.composite_btn.pack(side="left")

    def _create_predefined_section(self):
        """Create predefined materials section."""
        self.predefined_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        self.predefined_frame.pack(fill="x", pady=(0, 20))

        header = self.theme_manager.create_styled_label(
            self.predefined_frame,
            text="Predefined Materials",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 10))

        self.predefined_content = ctk.CTkFrame(
            self.predefined_frame,
            fg_color="transparent"
        )
        self.predefined_content.pack(fill="x", padx=20, pady=(0, 20))

    def _create_custom_section(self):
        """Create custom material definition section."""
        self.custom_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        self.custom_frame.pack(fill="x", pady=(0, 20))

        header = self.theme_manager.create_styled_label(
            self.custom_frame,
            text="Custom Material",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 10))

        self.custom_content = ctk.CTkFrame(
            self.custom_frame,
            fg_color="transparent"
        )
        self.custom_content.pack(fill="x", padx=20, pady=(0, 20))

        # Create form fields for isotropic material (default)
        self._create_isotropic_form()

    def _create_isotropic_form(self):
        """Create form for isotropic material properties."""
        # Clear existing content
        for widget in self.custom_content.winfo_children():
            widget.destroy()

        # Material name
        name_frame, name_label, self.name_entry = self.create_form_field(
            self.custom_content,
            "Material Name:",
            {"placeholder_text": "Enter material name"}
        )
        name_frame.pack(fill="x", pady=5)

        # Properties in two columns
        props_frame = ctk.CTkFrame(self.custom_content, fg_color="transparent")
        props_frame.pack(fill="x", pady=5)

        # Left column
        left_column = ctk.CTkFrame(props_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        e_frame, e_label, self.e_entry = self.create_form_field(
            left_column,
            "Young's Modulus (GPa):",
            {"placeholder_text": "71.7"}
        )
        e_frame.pack(fill="x")

        nu_frame, nu_label, self.nu_entry = self.create_form_field(
            left_column,
            "Poisson's Ratio:",
            {"placeholder_text": "0.33"}
        )
        nu_frame.pack(fill="x")

        g_frame, g_label, self.g_entry = self.create_form_field(
            left_column,
            "Shear Modulus (GPa):",
            {"placeholder_text": "26.9"}
        )
        g_frame.pack(fill="x")

        # Right column
        right_column = ctk.CTkFrame(props_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        rho_frame, rho_label, self.rho_entry = self.create_form_field(
            right_column,
            "Density (kg/m³):",
            {"placeholder_text": "2810"}
        )
        rho_frame.pack(fill="x")

        alpha_frame, alpha_label, self.alpha_entry = self.create_form_field(
            right_column,
            "Thermal Expansion (1/K):",
            {"placeholder_text": "21e-6 (optional)"}
        )
        alpha_frame.pack(fill="x")

        # Description
        desc_frame = ctk.CTkFrame(self.custom_content, fg_color="transparent")
        desc_frame.pack(fill="x", pady=5)

        desc_label = self.theme_manager.create_styled_label(
            desc_frame,
            text="Description (optional):",
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(anchor="w", pady=(0, 5))

        self.desc_text = ctk.CTkTextbox(desc_frame, height=60)
        self.desc_text.pack(fill="x")

        # Save button
        save_btn = self.theme_manager.create_styled_button(
            self.custom_content,
            text="💾 Save Material",
            command=self._save_custom_material,
            style="primary",
            height=35
        )
        save_btn.pack(pady=(15, 0))

    def _create_preview_section(self):
        """Create material preview section."""
        self.preview_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        self.preview_frame.pack(fill="x", pady=(0, 20))

        header = self.theme_manager.create_styled_label(
            self.preview_frame,
            text="Current Material",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 10))

        self.preview_content = ctk.CTkFrame(
            self.preview_frame,
            fg_color="transparent"
        )
        self.preview_content.pack(fill="x", padx=20, pady=(0, 20))

    def _create_navigation(self):
        """Create navigation buttons."""
        nav_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=20)

        # Back to home
        home_btn = self.theme_manager.create_styled_button(
            nav_frame,
            text="🏠 Home",
            command=lambda: self.main_window._show_panel("home"),
            style="secondary",
            width=120,
            height=35
        )
        home_btn.pack(side="left")

        # Next to geometry
        next_btn = self.theme_manager.create_styled_button(
            nav_frame,
            text="Next: Geometry ➡",
            command=lambda: self.main_window._show_panel("geometry"),
            style="primary",
            width=150,
            height=35
        )
        next_btn.pack(side="right")

        # Validate button
        validate_btn = self.theme_manager.create_styled_button(
            nav_frame,
            text="✓ Validate",
            command=self._validate_material,
            style="success",
            width=120,
            height=35
        )
        validate_btn.pack(side="right", padx=(0, 10))

    def _on_material_type_changed(self):
        """Handle material type change."""
        material_type = self.material_type_var.get()

        if material_type == "isotropic":
            self.current_material_type = MaterialType.ISOTROPIC
            self._create_isotropic_form()
        elif material_type == "orthotropic":
            self.current_material_type = MaterialType.ORTHOTROPIC
            self._create_orthotropic_form()
        elif material_type == "composite":
            self.current_material_type = MaterialType.COMPOSITE
            self._create_composite_form()

        self._refresh_predefined_materials()

    def _create_orthotropic_form(self):
        """Create form for orthotropic material properties."""
        # Clear existing content
        for widget in self.custom_content.winfo_children():
            widget.destroy()

        info_label = self.theme_manager.create_styled_label(
            self.custom_content,
            text="Orthotropic material form will be available in a future update.",
            text_color=self.theme_manager.get_color("text_secondary")
        )
        info_label.pack(pady=20)

    def _create_composite_form(self):
        """Create form for composite laminate properties."""
        # Clear existing content
        for widget in self.custom_content.winfo_children():
            widget.destroy()

        info_label = self.theme_manager.create_styled_label(
            self.custom_content,
            text="Composite laminate form will be available in a future update.",
            text_color=self.theme_manager.get_color("text_secondary")
        )
        info_label.pack(pady=20)

    def _refresh_predefined_materials(self):
        """Refresh predefined materials display."""
        # Clear existing content
        for widget in self.predefined_content.winfo_children():
            widget.destroy()

        if self.current_material_type == MaterialType.ISOTROPIC:
            materials = PredefinedMaterials.get_all_isotropic()
        elif self.current_material_type == MaterialType.ORTHOTROPIC:
            materials = PredefinedMaterials.get_all_orthotropic()
        else:
            # Composite - show info
            info_label = self.theme_manager.create_styled_label(
                self.predefined_content,
                text="Create custom composite laminates using the form below.",
                text_color=self.theme_manager.get_color("text_secondary")
            )
            info_label.pack(pady=10)
            return

        for material in materials:
            self._create_material_card(material)

    def _create_material_card(self, material):
        """Create a card for a predefined material."""
        card_frame = ctk.CTkFrame(
            self.predefined_content,
            corner_radius=8,
            fg_color=self.theme_manager.get_color("surface")
        )
        card_frame.pack(fill="x", pady=5)

        # Material info
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        name_label = self.theme_manager.create_styled_label(
            info_frame,
            text=material.name,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        name_label.pack(anchor="w")

        if hasattr(material, 'youngs_modulus'):
            # Isotropic material
            props_text = f"E = {material.youngs_modulus/1e9:.1f} GPa, ρ = {material.density:.0f} kg/m³"
        else:
            # Orthotropic material
            props_text = f"E1 = {material.e1/1e9:.1f} GPa, E2 = {material.e2/1e9:.1f} GPa"

        props_label = self.theme_manager.create_styled_label(
            info_frame,
            text=props_text,
            font=ctk.CTkFont(size=10),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        props_label.pack(anchor="w")

        if material.description:
            desc_label = self.theme_manager.create_styled_label(
                info_frame,
                text=material.description,
                font=ctk.CTkFont(size=10),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            desc_label.pack(anchor="w")

        # Select button
        select_btn = self.theme_manager.create_styled_button(
            card_frame,
            text="Select",
            command=lambda m=material: self._select_predefined_material(m),
            style="secondary",
            width=80,
            height=30
        )
        select_btn.pack(side="right", padx=15, pady=15)

    def _select_predefined_material(self, material):
        """Select a predefined material."""
        if self.project_manager.current_project:
            self.project_manager.current_project.material = material
            self._refresh_material_preview()
            self.main_window.update_status()
            self.show_info("Success", f"Selected material: {material.name}")
        else:
            self.show_warning("Warning", "Please create a project first.")

    def _save_custom_material(self):
        """Save custom material."""
        try:
            # Validate required fields
            name = self.name_entry.get().strip()
            if not name:
                self.show_error("Error", "Please enter a material name.")
                return

            if self.current_material_type == MaterialType.ISOTROPIC:
                # Get values
                e_str = self.e_entry.get().strip()
                nu_str = self.nu_entry.get().strip()
                g_str = self.g_entry.get().strip()
                rho_str = self.rho_entry.get().strip()
                alpha_str = self.alpha_entry.get().strip()

                if not all([e_str, nu_str, g_str, rho_str]):
                    self.show_error("Error", "Please fill in all required fields.")
                    return

                # Convert to numbers
                e = float(e_str) * 1e9  # Convert GPa to Pa
                nu = float(nu_str)
                g = float(g_str) * 1e9  # Convert GPa to Pa
                rho = float(rho_str)
                alpha = float(alpha_str) if alpha_str else None

                description = self.desc_text.get("1.0", "end").strip()

                # Create material
                material = IsotropicMaterial(
                    id=1,
                    name=name,
                    youngs_modulus=e,
                    poissons_ratio=nu,
                    shear_modulus=g,
                    density=rho,
                    thermal_expansion=alpha,
                    description=description if description else None
                )

                # Save to project
                if self.project_manager.current_project:
                    self.project_manager.current_project.material = material
                    self._refresh_material_preview()
                    self.main_window.update_status()
                    self.show_info("Success", f"Created material: {name}")
                else:
                    self.show_warning("Warning", "Please create a project first.")

            else:
                self.show_info("Info", "Custom orthotropic and composite materials will be available in a future update.")

        except ValueError as e:
            self.show_error("Error", f"Invalid input: {e}")
        except Exception as e:
            self.show_error("Error", f"Failed to create material: {e}")

    def _validate_material(self):
        """Validate current material."""
        if not self.project_manager.current_project:
            self.show_warning("Warning", "No project loaded.")
            return

        material = self.project_manager.current_project.material
        if not material:
            self.show_warning("Warning", "No material defined.")
            return

        # Basic validation
        errors = []

        if hasattr(material, 'youngs_modulus'):
            # Isotropic material validation
            if material.youngs_modulus <= 0:
                errors.append("Young's modulus must be positive")
            if not (0 <= material.poissons_ratio <= 0.5):
                errors.append("Poisson's ratio must be between 0 and 0.5")
            if material.shear_modulus <= 0:
                errors.append("Shear modulus must be positive")
            if material.density <= 0:
                errors.append("Density must be positive")

        if errors:
            error_msg = "Material validation errors:\n\n" + "\n".join(f"• {error}" for error in errors)
            self.show_error("Validation Error", error_msg)
        else:
            self.show_info("Validation", "Material properties are valid!")

    def _refresh_material_preview(self):
        """Refresh material preview display."""
        # Clear existing content
        for widget in self.preview_content.winfo_children():
            widget.destroy()

        if not self.project_manager.current_project or not self.project_manager.current_project.material:
            no_material_label = self.theme_manager.create_styled_label(
                self.preview_content,
                text="No material selected.",
                text_color=self.theme_manager.get_color("text_secondary")
            )
            no_material_label.pack(pady=10)
            return

        material = self.project_manager.current_project.material

        # Material name and type
        name_label = self.theme_manager.create_styled_label(
            self.preview_content,
            text=material.name,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.pack(anchor="w")

        if hasattr(material, 'youngs_modulus'):
            material_type = "Isotropic"
            props = [
                f"Young's Modulus: {material.youngs_modulus/1e9:.1f} GPa",
                f"Poisson's Ratio: {material.poissons_ratio:.3f}",
                f"Shear Modulus: {material.shear_modulus/1e9:.1f} GPa",
                f"Density: {material.density:.0f} kg/m³"
            ]
            if material.thermal_expansion:
                props.append(f"Thermal Expansion: {material.thermal_expansion:.2e} 1/K")
        else:
            material_type = "Orthotropic"
            props = [
                f"E1: {material.e1/1e9:.1f} GPa",
                f"E2: {material.e2/1e9:.1f} GPa",
                f"ν12: {material.nu12:.3f}",
                f"G12: {material.g12/1e9:.1f} GPa",
                f"Density: {material.density:.0f} kg/m³"
            ]

        type_label = self.theme_manager.create_styled_label(
            self.preview_content,
            text=f"Type: {material_type}",
            font=ctk.CTkFont(size=11),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        type_label.pack(anchor="w", pady=(5, 10))

        # Properties
        for prop in props:
            prop_label = self.theme_manager.create_styled_label(
                self.preview_content,
                text=prop,
                font=ctk.CTkFont(size=11)
            )
            prop_label.pack(anchor="w", pady=1)

        if material.description:
            desc_label = self.theme_manager.create_styled_label(
                self.preview_content,
                text=f"Description: {material.description}",
                font=ctk.CTkFont(size=11),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            desc_label.pack(anchor="w", pady=(10, 0))

    def _refresh_material_display(self):
        """Refresh all material-related displays."""
        self._refresh_predefined_materials()
        self._refresh_material_preview()

    def on_show(self):
        """Called when panel is shown."""
        self._refresh_material_display()
        self.main_window.update_status()

    def refresh(self):
        """Refresh the material panel."""
        self.on_show()