"""Material definition panel with advanced material types."""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List, Dict, Any
import tkinter as tk

from .base_panel import BasePanel
from models.material import (
    IsotropicMaterial, OrthotropicMaterial, CompositeLaminate,
    CompositeLamina, PredefinedMaterials, MaterialType
)

class MaterialPanel(BasePanel):
    """Panel for defining material properties with support for isotropic, orthotropic, and composite materials."""

    def __init__(self, parent, main_window):
        # Initialize composite tracking
        self.composite_layers = []
        self.current_layer_materials = {}
        super().__init__(parent, main_window)

    def _setup_ui(self):
        """Setup the material panel UI."""
        # Main scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.frame,
            corner_radius=0,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with gradient effect
        self._create_header()

        # Material type selection with beautiful tabs
        self._create_material_type_tabs()

        # Content area that changes based on selected type
        self.content_area = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, pady=20)

        # Navigation buttons
        self._create_navigation()

        # Initialize with isotropic material
        self.current_material_type = MaterialType.ISOTROPIC
        self._show_isotropic_content()

    def _create_header(self):
        """Create beautiful header section."""
        header_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        header_frame.pack(fill="x", pady=(0, 20))

        # Title with icon
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(fill="x", padx=25, pady=(20, 15))

        icon_label = self.theme_manager.create_styled_label(
            title_container,
            text="🔬",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(side="left", padx=(0, 15))

        title_frame = ctk.CTkFrame(title_container, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True)

        title_label = self.theme_manager.create_styled_label(
            title_frame,
            text="Material Properties",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = self.theme_manager.create_styled_label(
            title_frame,
            text="Define material properties for flutter analysis",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

    def _create_material_type_tabs(self):
        """Create beautiful material type selection tabs."""
        tabs_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        tabs_frame.pack(fill="x", pady=(0, 20))

        # Tab buttons container
        tab_container = ctk.CTkFrame(tabs_frame, fg_color="transparent")
        tab_container.pack(fill="x", padx=20, pady=20)

        self.tab_buttons = {}
        self.material_type_var = ctk.StringVar(value="isotropic")

        tabs_data = [
            ("isotropic", "🔧 Isotropic", "Uniform properties in all directions", self._show_isotropic_content),
            ("orthotropic", "📐 Orthotropic", "Different properties in principal directions", self._show_orthotropic_content),
            ("composite", "📚 Composite", "Layered composite laminate", self._show_composite_content)
        ]

        for i, (tab_id, label, description, command) in enumerate(tabs_data):
            tab_frame = ctk.CTkFrame(
                tab_container,
                fg_color=self.theme_manager.get_color("primary") if i == 0 else "transparent",
                border_color=self.theme_manager.get_color("border"),
                border_width=2,
                corner_radius=10
            )
            tab_frame.pack(side="left", fill="both", expand=True, padx=(0, 10) if i < 2 else 0)

            # Make frame clickable
            tab_frame.bind("<Button-1>", lambda e, t=tab_id, c=command: self._select_tab(t, c))

            # Tab content
            inner_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
            inner_frame.pack(padx=15, pady=12)
            inner_frame.bind("<Button-1>", lambda e, t=tab_id, c=command: self._select_tab(t, c))

            tab_label = self.theme_manager.create_styled_label(
                inner_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white" if i == 0 else self.theme_manager.get_color("text")
            )
            tab_label.pack(anchor="w")
            tab_label.bind("<Button-1>", lambda e, t=tab_id, c=command: self._select_tab(t, c))

            desc_label = self.theme_manager.create_styled_label(
                inner_frame,
                text=description,
                font=ctk.CTkFont(size=10),
                text_color="#e0e0e0" if i == 0 else self.theme_manager.get_color("text_secondary")
            )
            desc_label.pack(anchor="w")
            desc_label.bind("<Button-1>", lambda e, t=tab_id, c=command: self._select_tab(t, c))

            self.tab_buttons[tab_id] = tab_frame

    def _select_tab(self, tab_id: str, command):
        """Select a material type tab."""
        # Update visual state
        for tid, button in self.tab_buttons.items():
            if tid == tab_id:
                button.configure(fg_color=self.theme_manager.get_color("primary"))
                # Update text colors to white for selected tab
                for child in button.winfo_children():
                    for label in child.winfo_children():
                        if isinstance(label, ctk.CTkLabel):
                            if "bold" in str(label.cget("font")):
                                label.configure(text_color="white")
                            else:
                                label.configure(text_color="#e0e0e0")
            else:
                button.configure(fg_color="transparent")
                # Update text colors to normal for unselected tabs
                for child in button.winfo_children():
                    for label in child.winfo_children():
                        if isinstance(label, ctk.CTkLabel):
                            if "bold" in str(label.cget("font")):
                                label.configure(text_color=self.theme_manager.get_color("text"))
                            else:
                                label.configure(text_color=self.theme_manager.get_color("text_secondary"))

        self.material_type_var.set(tab_id)
        command()

    def _show_isotropic_content(self):
        """Show isotropic material content."""
        self.current_material_type = MaterialType.ISOTROPIC
        self._clear_content_area()

        # Create two-column layout
        columns_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        columns_frame.pack(fill="both", expand=True)

        # Left column - Predefined materials
        left_column = ctk.CTkFrame(columns_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._create_predefined_isotropic_section(left_column)

        # Right column - Custom material
        right_column = ctk.CTkFrame(columns_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self._create_custom_isotropic_section(right_column)

    def _create_predefined_isotropic_section(self, parent):
        """Create predefined isotropic materials section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="both", expand=True)

        header = self.theme_manager.create_styled_label(
            frame,
            text="📚 Predefined Materials",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 15))

        # Scrollable list of materials
        materials_scroll = ctk.CTkScrollableFrame(frame, height=400)
        materials_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        materials = PredefinedMaterials.get_all_isotropic()
        for material in materials:
            self._create_material_card(materials_scroll, material)

    def _create_material_card(self, parent, material):
        """Create a beautiful material card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme_manager.get_color("surface"),
            corner_radius=10
        )
        card.pack(fill="x", pady=5)

        # Material icon based on type
        icon_map = {
            "Aluminum": "✈️",
            "Steel": "🔩",
            "Titanium": "🚀",
            "Magnesium": "⚡",
            "Carbon": "🔷",
            "Glass": "🔮"
        }
        icon = next((v for k, v in icon_map.items() if k in material.name), "📦")

        icon_label = self.theme_manager.create_styled_label(
            card,
            text=icon,
            font=ctk.CTkFont(size=24)
        )
        icon_label.pack(side="left", padx=(15, 10), pady=15)

        # Material info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)

        name_label = self.theme_manager.create_styled_label(
            info_frame,
            text=material.name,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        name_label.pack(anchor="w")

        if hasattr(material, 'youngs_modulus'):
            props_text = f"E = {material.youngs_modulus/1e9:.1f} GPa | ρ = {material.density:.0f} kg/m³ | ν = {material.poissons_ratio:.2f}"
        else:
            props_text = f"E₁ = {material.e1/1e9:.1f} GPa | E₂ = {material.e2/1e9:.1f} GPa"

        props_label = self.theme_manager.create_styled_label(
            info_frame,
            text=props_text,
            font=ctk.CTkFont(size=10),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        props_label.pack(anchor="w", pady=(2, 0))

        # Select button
        select_btn = ctk.CTkButton(
            card,
            text="Select",
            command=lambda m=material: self._select_material(m),
            width=80,
            height=30,
            corner_radius=6
        )
        select_btn.pack(side="right", padx=15, pady=15)

    def _create_custom_isotropic_section(self, parent):
        """Create custom isotropic material section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="both", expand=True)

        header = self.theme_manager.create_styled_label(
            frame,
            text="✏️ Custom Material",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 15))

        # Form container
        form_frame = ctk.CTkFrame(frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Material name
        self._create_input_field(form_frame, "Material Name:", "name_entry", "Enter material name")

        # Properties grid
        props_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        props_frame.pack(fill="x", pady=(10, 0))

        # Young's modulus
        self._create_input_field(props_frame, "Young's Modulus (GPa):", "e_entry", "71.7")

        # Poisson's ratio
        self._create_input_field(props_frame, "Poisson's Ratio:", "nu_entry", "0.33")

        # Shear modulus
        self._create_input_field(props_frame, "Shear Modulus (GPa):", "g_entry", "26.9")

        # Density
        self._create_input_field(props_frame, "Density (kg/m³):", "rho_entry", "2810")

        # Thermal expansion (optional)
        self._create_input_field(props_frame, "Thermal Expansion (1/K):", "alpha_entry", "21e-6 (optional)")

        # Save button
        save_btn = ctk.CTkButton(
            form_frame,
            text="💾 Save Material",
            command=self._save_isotropic_material,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(pady=(20, 0))

    def _show_orthotropic_content(self):
        """Show orthotropic material content."""
        self.current_material_type = MaterialType.ORTHOTROPIC
        self._clear_content_area()

        # Create two-column layout
        columns_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        columns_frame.pack(fill="both", expand=True)

        # Left column - Predefined materials
        left_column = ctk.CTkFrame(columns_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._create_predefined_orthotropic_section(left_column)

        # Right column - Custom material
        right_column = ctk.CTkFrame(columns_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self._create_custom_orthotropic_section(right_column)

    def _create_predefined_orthotropic_section(self, parent):
        """Create predefined orthotropic materials section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="both", expand=True)

        header = self.theme_manager.create_styled_label(
            frame,
            text="📚 Predefined Orthotropic Materials",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 15))

        # Scrollable list
        materials_scroll = ctk.CTkScrollableFrame(frame, height=400)
        materials_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Get orthotropic materials
        materials = PredefinedMaterials.get_all_orthotropic()
        for material in materials:
            self._create_material_card(materials_scroll, material)

    def _create_custom_orthotropic_section(self, parent):
        """Create custom orthotropic material section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="both", expand=True)

        header = self.theme_manager.create_styled_label(
            frame,
            text="✏️ Custom Orthotropic Material",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 15))

        # Form container with scroll
        form_scroll = ctk.CTkScrollableFrame(frame, height=400)
        form_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Material name
        self._create_input_field(form_scroll, "Material Name:", "ortho_name_entry", "Custom Orthotropic")

        # Direction 1 properties
        dir1_label = self.theme_manager.create_styled_label(
            form_scroll,
            text="Direction 1 Properties",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        dir1_label.pack(anchor="w", pady=(15, 5))

        self._create_input_field(form_scroll, "E₁ - Young's Modulus (GPa):", "e1_entry", "130.0")
        self._create_input_field(form_scroll, "α₁ - Thermal Expansion (1/K):", "alpha1_entry", "2e-6 (optional)")

        # Direction 2 properties
        dir2_label = self.theme_manager.create_styled_label(
            form_scroll,
            text="Direction 2 Properties",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        dir2_label.pack(anchor="w", pady=(15, 5))

        self._create_input_field(form_scroll, "E₂ - Young's Modulus (GPa):", "e2_entry", "10.5")
        self._create_input_field(form_scroll, "α₂ - Thermal Expansion (1/K):", "alpha2_entry", "22e-6 (optional)")

        # Shear properties
        shear_label = self.theme_manager.create_styled_label(
            form_scroll,
            text="Shear Properties",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        shear_label.pack(anchor="w", pady=(15, 5))

        self._create_input_field(form_scroll, "ν₁₂ - Poisson's Ratio:", "nu12_entry", "0.28")
        self._create_input_field(form_scroll, "G₁₂ - In-plane Shear (GPa):", "g12_entry", "5.5")
        self._create_input_field(form_scroll, "G₁z - Out-of-plane Shear (GPa):", "g1z_entry", "5.5 (optional)")
        self._create_input_field(form_scroll, "G₂z - Out-of-plane Shear (GPa):", "g2z_entry", "3.5 (optional)")

        # General properties
        general_label = self.theme_manager.create_styled_label(
            form_scroll,
            text="General Properties",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        general_label.pack(anchor="w", pady=(15, 5))

        self._create_input_field(form_scroll, "Density (kg/m³):", "ortho_rho_entry", "1600")

        # Save button
        save_btn = ctk.CTkButton(
            form_scroll,
            text="💾 Save Orthotropic Material",
            command=self._save_orthotropic_material,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(pady=(20, 10))

    def _show_composite_content(self):
        """Show composite laminate content."""
        self.current_material_type = MaterialType.COMPOSITE
        self._clear_content_area()

        # Main container
        main_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        # Top section - Laminate builder
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 20))

        self._create_laminate_builder(top_frame)

        # Bottom section - Layer list
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True)

        self._create_layer_list(bottom_frame)

    def _create_laminate_builder(self, parent):
        """Create composite laminate builder section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="x")

        header = self.theme_manager.create_styled_label(
            frame,
            text="🔨 Laminate Builder",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(20, 15))

        # Laminate info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(0, 15))

        self._create_input_field(info_frame, "Laminate Name:", "laminate_name_entry", "Custom Composite")

        # Add layer section
        add_layer_frame = ctk.CTkFrame(frame, fg_color=self.theme_manager.get_color("surface"), corner_radius=10)
        add_layer_frame.pack(fill="x", padx=20, pady=(0, 20))

        add_header = self.theme_manager.create_styled_label(
            add_layer_frame,
            text="Add New Layer",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        add_header.pack(anchor="w", padx=15, pady=(15, 10))

        # Layer properties in grid
        props_frame = ctk.CTkFrame(add_layer_frame, fg_color="transparent")
        props_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Material selection
        mat_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        mat_frame.pack(fill="x", pady=5)

        mat_label = self.theme_manager.create_styled_label(
            mat_frame,
            text="Material:",
            font=ctk.CTkFont(size=12),
            width=100
        )
        mat_label.pack(side="left")

        # Get available materials for layers
        layer_materials = ["T300/5208 Carbon/Epoxy", "E-Glass/Epoxy", "S-Glass/Epoxy", "Kevlar-49/Epoxy"]
        self.layer_material_var = ctk.StringVar(value=layer_materials[0])
        mat_combo = ctk.CTkComboBox(
            mat_frame,
            variable=self.layer_material_var,
            values=layer_materials,
            width=250
        )
        mat_combo.pack(side="left", padx=(10, 0))

        # Thickness
        thick_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        thick_frame.pack(fill="x", pady=5)

        thick_label = self.theme_manager.create_styled_label(
            thick_frame,
            text="Thickness (mm):",
            font=ctk.CTkFont(size=12),
            width=100
        )
        thick_label.pack(side="left")

        self.layer_thickness_entry = ctk.CTkEntry(
            thick_frame,
            placeholder_text="0.125",
            width=250
        )
        self.layer_thickness_entry.pack(side="left", padx=(10, 0))

        # Orientation
        orient_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        orient_frame.pack(fill="x", pady=5)

        orient_label = self.theme_manager.create_styled_label(
            orient_frame,
            text="Orientation (°):",
            font=ctk.CTkFont(size=12),
            width=100
        )
        orient_label.pack(side="left")

        self.layer_orientation_entry = ctk.CTkEntry(
            orient_frame,
            placeholder_text="0, 45, 90, -45",
            width=250
        )
        self.layer_orientation_entry.pack(side="left", padx=(10, 0))

        # Add layer button
        add_btn = ctk.CTkButton(
            add_layer_frame,
            text="➕ Add Layer",
            command=self._add_composite_layer,
            height=35,
            corner_radius=6
        )
        add_btn.pack(pady=(0, 10))

    def _create_layer_list(self, parent):
        """Create composite layer list section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="both", expand=True)

        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))

        list_header = self.theme_manager.create_styled_label(
            header_frame,
            text="📋 Layer Stack",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_header.pack(side="left")

        self.total_thickness_label = self.theme_manager.create_styled_label(
            header_frame,
            text="Total: 0.0 mm",
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        self.total_thickness_label.pack(side="right")

        # Layer list with scroll
        self.layers_scroll = ctk.CTkScrollableFrame(frame, height=250)
        self.layers_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Control buttons
        control_frame = ctk.CTkFrame(frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(0, 20))

        clear_btn = ctk.CTkButton(
            control_frame,
            text="🗑️ Clear All",
            command=self._clear_layers,
            fg_color="transparent",
            border_width=2,
            border_color=self.theme_manager.get_color("border"),
            height=35,
            width=120
        )
        clear_btn.pack(side="left", padx=(0, 10))

        sym_btn = ctk.CTkButton(
            control_frame,
            text="↔️ Make Symmetric",
            command=self._make_symmetric,
            fg_color="transparent",
            border_width=2,
            border_color=self.theme_manager.get_color("border"),
            height=35,
            width=140
        )
        sym_btn.pack(side="left", padx=(0, 10))

        save_btn = ctk.CTkButton(
            control_frame,
            text="💾 Save Laminate",
            command=self._save_composite_material,
            height=35,
            corner_radius=6
        )
        save_btn.pack(side="right")

    def _create_input_field(self, parent, label_text: str, entry_name: str, placeholder: str = ""):
        """Create a styled input field."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        label = self.theme_manager.create_styled_label(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=12)
        )
        label.pack(anchor="w", pady=(0, 5))

        entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            height=35
        )
        entry.pack(fill="x")

        # Store reference
        setattr(self, entry_name, entry)

        return frame, label, entry

    def _clear_content_area(self):
        """Clear the content area."""
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def _select_material(self, material):
        """Select a predefined material."""
        if self.project_manager.current_project:
            self.project_manager.current_project.material = material
            self.main_window.update_status()
            self.show_info("Success", f"Selected material: {material.name}")
        else:
            self.show_warning("Warning", "Please create a project first.")

    def _save_isotropic_material(self):
        """Save custom isotropic material."""
        try:
            name = self.name_entry.get().strip()
            if not name:
                self.show_error("Error", "Please enter a material name.")
                return

            # Get values
            e = float(self.e_entry.get()) * 1e9  # GPa to Pa
            nu = float(self.nu_entry.get())
            g = float(self.g_entry.get()) * 1e9  # GPa to Pa
            rho = float(self.rho_entry.get())

            alpha_text = self.alpha_entry.get().strip()
            alpha = float(alpha_text.replace("(optional)", "").strip()) if alpha_text and "optional" not in alpha_text else None

            # Create material
            material = IsotropicMaterial(
                id=1,
                name=name,
                youngs_modulus=e,
                poissons_ratio=nu,
                shear_modulus=g,
                density=rho,
                thermal_expansion=alpha
            )

            # Save to project
            if self.project_manager.current_project:
                self.project_manager.current_project.material = material
                self.main_window.update_status()
                self.show_info("Success", f"Created isotropic material: {name}")
            else:
                self.show_warning("Warning", "Please create a project first.")

        except ValueError as e:
            self.show_error("Error", f"Invalid input: Please enter valid numbers")
        except Exception as e:
            self.show_error("Error", f"Failed to create material: {e}")

    def _save_orthotropic_material(self):
        """Save custom orthotropic material."""
        try:
            name = self.ortho_name_entry.get().strip()
            if not name:
                self.show_error("Error", "Please enter a material name.")
                return

            # Get values
            e1 = float(self.e1_entry.get()) * 1e9  # GPa to Pa
            e2 = float(self.e2_entry.get()) * 1e9  # GPa to Pa
            nu12 = float(self.nu12_entry.get())
            g12 = float(self.g12_entry.get()) * 1e9  # GPa to Pa
            rho = float(self.ortho_rho_entry.get())

            # Optional values
            alpha1_text = self.alpha1_entry.get().strip()
            alpha1 = float(alpha1_text.replace("(optional)", "").strip()) if alpha1_text and "optional" not in alpha1_text else None

            alpha2_text = self.alpha2_entry.get().strip()
            alpha2 = float(alpha2_text.replace("(optional)", "").strip()) if alpha2_text and "optional" not in alpha2_text else None

            g1z_text = self.g1z_entry.get().strip()
            g1z = float(g1z_text.replace("(optional)", "").strip()) * 1e9 if g1z_text and "optional" not in g1z_text else None

            g2z_text = self.g2z_entry.get().strip()
            g2z = float(g2z_text.replace("(optional)", "").strip()) * 1e9 if g2z_text and "optional" not in g2z_text else None

            # Create material
            material = OrthotropicMaterial(
                id=1,
                name=name,
                e1=e1,
                e2=e2,
                nu12=nu12,
                g12=g12,
                density=rho,
                alpha1=alpha1,
                alpha2=alpha2,
                g1z=g1z,
                g2z=g2z
            )

            # Save to project
            if self.project_manager.current_project:
                self.project_manager.current_project.material = material
                self.main_window.update_status()
                self.show_info("Success", f"Created orthotropic material: {name}")
            else:
                self.show_warning("Warning", "Please create a project first.")

        except ValueError as e:
            self.show_error("Error", f"Invalid input: Please enter valid numbers")
        except Exception as e:
            self.show_error("Error", f"Failed to create material: {e}")

    def _add_composite_layer(self):
        """Add a layer to the composite laminate."""
        try:
            material_name = self.layer_material_var.get()
            thickness = float(self.layer_thickness_entry.get() or "0.125")
            orientation_text = self.layer_orientation_entry.get() or "0"

            # Parse orientations (can be comma-separated)
            orientations = [float(x.strip()) for x in orientation_text.split(",")]

            # Get or create material for layer
            if material_name not in self.current_layer_materials:
                # Create a simple orthotropic material for the layer
                self.current_layer_materials[material_name] = self._create_layer_material(material_name)

            material = self.current_layer_materials[material_name]

            # Add layers for each orientation
            for orientation in orientations:
                layer = {
                    'material': material,
                    'material_name': material_name,
                    'thickness': thickness,
                    'orientation': orientation
                }
                self.composite_layers.append(layer)

            # Update display
            self._update_layer_display()

            # Clear inputs
            self.layer_thickness_entry.delete(0, 'end')
            self.layer_orientation_entry.delete(0, 'end')

        except ValueError as e:
            self.show_error("Error", "Please enter valid numbers for thickness and orientation")
        except Exception as e:
            self.show_error("Error", f"Failed to add layer: {e}")

    def _create_layer_material(self, name: str) -> OrthotropicMaterial:
        """Create a predefined layer material."""
        # Predefined properties for common composite materials
        materials_db = {
            "T300/5208 Carbon/Epoxy": {
                "e1": 181e9, "e2": 10.3e9, "nu12": 0.28,
                "g12": 7.17e9, "density": 1600
            },
            "E-Glass/Epoxy": {
                "e1": 38.6e9, "e2": 8.27e9, "nu12": 0.26,
                "g12": 4.14e9, "density": 1900
            },
            "S-Glass/Epoxy": {
                "e1": 43.0e9, "e2": 8.9e9, "nu12": 0.27,
                "g12": 4.5e9, "density": 2000
            },
            "Kevlar-49/Epoxy": {
                "e1": 80e9, "e2": 5.5e9, "nu12": 0.34,
                "g12": 2.2e9, "density": 1380
            }
        }

        props = materials_db.get(name, materials_db["T300/5208 Carbon/Epoxy"])

        return OrthotropicMaterial(
            id=len(self.current_layer_materials) + 1,
            name=name,
            e1=props["e1"],
            e2=props["e2"],
            nu12=props["nu12"],
            g12=props["g12"],
            density=props["density"]
        )

    def _update_layer_display(self):
        """Update the layer stack display."""
        # Clear existing display
        for widget in self.layers_scroll.winfo_children():
            widget.destroy()

        # Display each layer
        total_thickness = 0
        for i, layer in enumerate(self.composite_layers):
            layer_frame = ctk.CTkFrame(
                self.layers_scroll,
                fg_color=self.theme_manager.get_color("surface"),
                corner_radius=8
            )
            layer_frame.pack(fill="x", pady=2)

            # Layer number
            num_label = self.theme_manager.create_styled_label(
                layer_frame,
                text=f"#{i+1}",
                font=ctk.CTkFont(size=12, weight="bold"),
                width=40
            )
            num_label.pack(side="left", padx=(15, 10), pady=10)

            # Layer info
            info_text = f"{layer['material_name']} | {layer['thickness']} mm | {layer['orientation']}°"
            info_label = self.theme_manager.create_styled_label(
                layer_frame,
                text=info_text,
                font=ctk.CTkFont(size=11)
            )
            info_label.pack(side="left", fill="x", expand=True, pady=10)

            # Remove button
            remove_btn = ctk.CTkButton(
                layer_frame,
                text="❌",
                command=lambda idx=i: self._remove_layer(idx),
                width=30,
                height=30,
                fg_color="transparent"
            )
            remove_btn.pack(side="right", padx=10, pady=10)

            total_thickness += layer['thickness']

        # Update total thickness
        self.total_thickness_label.configure(text=f"Total: {total_thickness:.2f} mm")

    def _remove_layer(self, index: int):
        """Remove a layer from the composite."""
        if 0 <= index < len(self.composite_layers):
            self.composite_layers.pop(index)
            self._update_layer_display()

    def _clear_layers(self):
        """Clear all layers."""
        self.composite_layers = []
        self._update_layer_display()

    def _make_symmetric(self):
        """Make the laminate symmetric."""
        if not self.composite_layers:
            self.show_warning("Warning", "No layers to make symmetric")
            return

        # Duplicate layers in reverse order (excluding middle if odd number)
        original_layers = self.composite_layers.copy()

        # Add reversed layers
        for layer in reversed(original_layers[:-1]):
            self.composite_layers.append(layer.copy())

        self._update_layer_display()

    def _save_composite_material(self):
        """Save composite laminate."""
        try:
            if not self.composite_layers:
                self.show_error("Error", "Please add at least one layer")
                return

            name = self.laminate_name_entry.get().strip() or "Custom Composite"

            # Create lamina objects
            laminas = []
            for i, layer in enumerate(self.composite_layers):
                lamina = CompositeLamina(
                    id=i+1,
                    material=layer['material'],
                    thickness=layer['thickness'],
                    orientation=layer['orientation']
                )
                laminas.append(lamina)

            # Create laminate
            laminate = CompositeLaminate(
                id=1,
                name=name,
                laminas=laminas
            )

            # Save to project
            if self.project_manager.current_project:
                self.project_manager.current_project.material = laminate
                self.main_window.update_status()
                self.show_info("Success", f"Created composite laminate: {name}\nTotal thickness: {laminate.total_thickness:.2f} mm")
            else:
                self.show_warning("Warning", "Please create a project first.")

        except Exception as e:
            self.show_error("Error", f"Failed to create laminate: {e}")

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

        # Next to structure
        next_btn = self.theme_manager.create_styled_button(
            nav_frame,
            text="Next: Structure ➡",
            command=lambda: self.main_window._show_panel("structure"),
            style="primary",
            width=150,
            height=35
        )
        next_btn.pack(side="right")

    def on_show(self):
        """Called when panel is shown."""
        self.main_window.update_status()

    def refresh(self):
        """Refresh the material panel."""
        self.on_show()