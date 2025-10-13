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

        # Project status warning (if no project exists)
        self._create_project_status_warning()

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

    def _create_project_status_warning(self):
        """Create project status warning if no project exists."""
        # Container for warning (we'll update visibility later)
        self.project_warning_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="#ff6b6b",
            corner_radius=10
        )

        # Warning content
        warning_content = ctk.CTkFrame(self.project_warning_frame, fg_color="transparent")
        warning_content.pack(fill="x", padx=20, pady=15)

        # Icon and message
        icon_label = self.theme_manager.create_styled_label(
            warning_content,
            text="⚠️",
            font=ctk.CTkFont(size=24),
            text_color="white"
        )
        icon_label.pack(side="left", padx=(0, 15))

        text_frame = ctk.CTkFrame(warning_content, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        title_label = self.theme_manager.create_styled_label(
            text_frame,
            text="No Project Created",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        title_label.pack(anchor="w")

        msg_label = self.theme_manager.create_styled_label(
            text_frame,
            text="You must create a project before adding custom materials. Predefined materials can still be selected.",
            font=ctk.CTkFont(size=11),
            text_color="#ffe0e0"
        )
        msg_label.pack(anchor="w", pady=(2, 0))

        # Create project button
        create_btn = ctk.CTkButton(
            warning_content,
            text="📁 Create Project",
            command=self._quick_create_project,
            fg_color="white",
            text_color="#ff6b6b",
            hover_color="#f0f0f0",
            height=35,
            width=140,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        create_btn.pack(side="right", padx=(15, 0))

        # Initially hide if project exists, show if not
        self._update_project_warning_visibility()

    def _quick_create_project(self):
        """Quick project creation from material panel."""
        # Navigate to home panel and trigger new project dialog
        self.main_window._show_panel("home")
        if "home" in self.main_window.panels:
            self.main_window.panels["home"].show_new_project_dialog()

    def _update_project_warning_visibility(self):
        """Update visibility of project warning based on project status."""
        if self.project_manager.current_project:
            self.project_warning_frame.pack_forget()
        else:
            self.project_warning_frame.pack(fill="x", pady=(0, 20))

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
            ("composite", "📚 Composite", "Layered composite laminate", self._show_composite_content),
            ("sandwich", "🥪 Sandwich", "Honeycomb core with face sheets", self._show_sandwich_content)
        ]

        for i, (tab_id, label, description, command) in enumerate(tabs_data):
            tab_frame = ctk.CTkFrame(
                tab_container,
                fg_color=self.theme_manager.get_color("primary") if i == 0 else "transparent",
                border_color=self.theme_manager.get_color("border"),
                border_width=2,
                corner_radius=10
            )
            tab_frame.pack(side="left", fill="both", expand=True, padx=(0, 10) if i < 3 else 0)

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

        # REMOVED: Thermal expansion - not used in flutter analysis

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

        # Initialize custom prepreg materials in project if not present
        if self.project_manager.current_project:
            if self.project_manager.current_project.custom_prepreg_materials is None:
                self.project_manager.current_project.custom_prepreg_materials = []

        # Main container
        main_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        # Top section - Custom prepreg materials management
        custom_mat_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        custom_mat_frame.pack(fill="x", pady=(0, 20))

        self._create_custom_prepreg_section(custom_mat_frame)

        # Middle section - Laminate builder
        middle_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        middle_frame.pack(fill="x", pady=(0, 20))

        self._create_laminate_builder(middle_frame)

        # Bottom section - Layer list
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True)

        self._create_layer_list(bottom_frame)

    def _create_custom_prepreg_section(self, parent):
        """Create custom prepreg material management section."""
        frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        frame.pack(fill="x")

        # Header with toggle button
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))

        header = self.theme_manager.create_styled_label(
            header_frame,
            text="🎨 Custom Prepreg Materials",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(side="left")

        # Expandable section toggle
        self.prepreg_section_expanded = False
        self.toggle_prepreg_btn = ctk.CTkButton(
            header_frame,
            text="▼ Show",
            command=self._toggle_prepreg_section,
            width=100,
            height=30,
            fg_color="transparent",
            border_width=2,
            border_color=self.theme_manager.get_color("border")
        )
        self.toggle_prepreg_btn.pack(side="right")

        # Expandable content frame
        self.prepreg_content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        # Initially hidden

        # Add prepreg form
        form_frame = ctk.CTkFrame(self.prepreg_content_frame,
                                  fg_color=self.theme_manager.get_color("surface"),
                                  corner_radius=10)
        form_frame.pack(fill="x", padx=20, pady=(0, 15))

        form_header = self.theme_manager.create_styled_label(
            form_frame,
            text="Add New Prepreg Material",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        form_header.pack(anchor="w", padx=15, pady=(15, 10))

        # Form fields in a scrollable area
        form_scroll = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_scroll.pack(fill="x", padx=15, pady=(0, 15))

        # Material name
        self._create_input_field(form_scroll, "Material Name:", "prepreg_name_entry", "e.g., AS4/3501-6")

        # Create two columns for properties
        cols_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        cols_frame.pack(fill="x", pady=(10, 0))

        left_col = ctk.CTkFrame(cols_frame, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        right_col = ctk.CTkFrame(cols_frame, fg_color="transparent")
        right_col.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Left column - Elastic properties
        elastic_label = self.theme_manager.create_styled_label(
            left_col,
            text="Elastic Properties",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        elastic_label.pack(anchor="w", pady=(5, 5))

        self._create_input_field(left_col, "E₁ (GPa):", "prepreg_e1_entry", "130.0")
        self._create_input_field(left_col, "E₂ (GPa):", "prepreg_e2_entry", "10.5")
        self._create_input_field(left_col, "ν₁₂:", "prepreg_nu12_entry", "0.28")
        self._create_input_field(left_col, "G₁₂ (GPa):", "prepreg_g12_entry", "5.5")

        # Right column - Additional properties
        additional_label = self.theme_manager.create_styled_label(
            right_col,
            text="Additional Properties",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        additional_label.pack(anchor="w", pady=(5, 5))

        self._create_input_field(right_col, "Density (kg/m³):", "prepreg_density_entry", "1600")
        self._create_input_field(right_col, "G₁z (GPa) [optional]:", "prepreg_g1z_entry", "")
        self._create_input_field(right_col, "G₂z (GPa) [optional]:", "prepreg_g2z_entry", "")

        # Add button
        add_prepreg_btn = ctk.CTkButton(
            form_frame,
            text="➕ Add Prepreg Material",
            command=self._add_custom_prepreg,
            height=35,
            corner_radius=6,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        add_prepreg_btn.pack(pady=(0, 15))

        # List of custom prepregs
        list_frame = ctk.CTkFrame(self.prepreg_content_frame,
                                  fg_color=self.theme_manager.get_color("surface"),
                                  corner_radius=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        list_header = self.theme_manager.create_styled_label(
            list_frame,
            text="Your Custom Prepreg Materials",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_header.pack(anchor="w", padx=15, pady=(15, 10))

        # Scrollable list
        self.custom_prepreg_list_frame = ctk.CTkScrollableFrame(list_frame, height=150)
        self.custom_prepreg_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Update the list
        self._update_custom_prepreg_list()

    def _toggle_prepreg_section(self):
        """Toggle the custom prepreg section visibility."""
        self.prepreg_section_expanded = not self.prepreg_section_expanded

        if self.prepreg_section_expanded:
            self.prepreg_content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            self.toggle_prepreg_btn.configure(text="▲ Hide")
        else:
            self.prepreg_content_frame.pack_forget()
            self.toggle_prepreg_btn.configure(text="▼ Show")

    def _add_custom_prepreg(self):
        """Add a custom prepreg material."""
        if not self.project_manager.current_project:
            self.show_warning("Warning", "Please create a project first.\n\nClick 'Create Project' button at the top of this page.")
            return

        try:
            # Get and validate material name
            name = self.prepreg_name_entry.get().strip()
            if not name:
                self.show_error("Validation Error", "Please enter a material name.")
                return

            # Check for duplicate names
            if self.project_manager.current_project.custom_prepreg_materials:
                existing_names = [m.name for m in self.project_manager.current_project.custom_prepreg_materials]
                if name in existing_names:
                    self.show_error("Duplicate Material", f"A material named '{name}' already exists.\nPlease use a different name.")
                    return

            # Get and validate properties
            e1 = float(self.prepreg_e1_entry.get()) * 1e9  # GPa to Pa
            e2 = float(self.prepreg_e2_entry.get()) * 1e9
            nu12 = float(self.prepreg_nu12_entry.get())
            g12 = float(self.prepreg_g12_entry.get()) * 1e9
            density = float(self.prepreg_density_entry.get())

            # Validate ranges
            if e1 <= 0 or e2 <= 0:
                self.show_error("Validation Error", "Young's moduli (E₁, E₂) must be positive.")
                return

            if nu12 <= 0 or nu12 >= 1:
                self.show_error("Validation Error", "Poisson's ratio (ν₁₂) must be between 0 and 1.")
                return

            if g12 <= 0:
                self.show_error("Validation Error", "Shear modulus (G₁₂) must be positive.")
                return

            if density <= 0:
                self.show_error("Validation Error", "Density must be positive.")
                return

            # Optional properties
            g1z_text = self.prepreg_g1z_entry.get().strip()
            g1z = float(g1z_text) * 1e9 if g1z_text else None

            g2z_text = self.prepreg_g2z_entry.get().strip()
            g2z = float(g2z_text) * 1e9 if g2z_text else None

            # Create material
            material = OrthotropicMaterial(
                id=len(self.project_manager.current_project.custom_prepreg_materials) + 100,
                name=name,
                e1=e1,
                e2=e2,
                nu12=nu12,
                g12=g12,
                density=density,
                g1z=g1z,
                g2z=g2z,
                description="Custom prepreg material"
            )

            # Add to project
            self.project_manager.current_project.custom_prepreg_materials.append(material)
            self.project_manager.save_current_project()

            # Update UI
            self._update_custom_prepreg_list()
            self._update_layer_material_dropdown()

            # Clear form
            self.prepreg_name_entry.delete(0, 'end')
            self.prepreg_e1_entry.delete(0, 'end')
            self.prepreg_e2_entry.delete(0, 'end')
            self.prepreg_nu12_entry.delete(0, 'end')
            self.prepreg_g12_entry.delete(0, 'end')
            self.prepreg_density_entry.delete(0, 'end')
            self.prepreg_g1z_entry.delete(0, 'end')
            self.prepreg_g2z_entry.delete(0, 'end')

            self.show_info("Success", f"Added custom prepreg material: {name}")

        except ValueError as e:
            self.show_error("Invalid Input", "Please enter valid numbers for all material properties.")
        except Exception as e:
            self.show_error("Error", f"Failed to add material: {e}")

    def _update_custom_prepreg_list(self):
        """Update the list of custom prepreg materials."""
        # Clear existing
        for widget in self.custom_prepreg_list_frame.winfo_children():
            widget.destroy()

        if not self.project_manager.current_project or \
           not self.project_manager.current_project.custom_prepreg_materials:
            # Show empty message
            empty_label = self.theme_manager.create_styled_label(
                self.custom_prepreg_list_frame,
                text="No custom prepreg materials yet. Add one above!",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            empty_label.pack(pady=20)
            return

        # Display each material
        for material in self.project_manager.current_project.custom_prepreg_materials:
            mat_card = ctk.CTkFrame(
                self.custom_prepreg_list_frame,
                fg_color=self.theme_manager.get_color("background"),
                corner_radius=8
            )
            mat_card.pack(fill="x", pady=3)

            # Material info
            info_frame = ctk.CTkFrame(mat_card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)

            name_label = self.theme_manager.create_styled_label(
                info_frame,
                text=material.name,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            name_label.pack(anchor="w")

            props_text = f"E₁={material.e1/1e9:.1f} GPa | E₂={material.e2/1e9:.1f} GPa | ν₁₂={material.nu12:.2f} | ρ={material.density:.0f} kg/m³"
            props_label = self.theme_manager.create_styled_label(
                info_frame,
                text=props_text,
                font=ctk.CTkFont(size=10),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            props_label.pack(anchor="w", pady=(2, 0))

            # Delete button
            delete_btn = ctk.CTkButton(
                mat_card,
                text="🗑️",
                command=lambda m=material: self._delete_custom_prepreg(m),
                width=35,
                height=35,
                fg_color="transparent",
                hover_color="#ff6b6b"
            )
            delete_btn.pack(side="right", padx=10, pady=10)

    def _delete_custom_prepreg(self, material):
        """Delete a custom prepreg material."""
        if not self.project_manager.current_project:
            return

        try:
            # Confirm deletion
            if messagebox.askyesno("Confirm Deletion",
                                  f"Delete custom prepreg material '{material.name}'?\n\nThis action cannot be undone."):
                self.project_manager.current_project.custom_prepreg_materials.remove(material)
                self.project_manager.save_current_project()

                # Update UI
                self._update_custom_prepreg_list()
                self._update_layer_material_dropdown()

                self.show_info("Deleted", f"Removed material: {material.name}")

        except Exception as e:
            self.show_error("Error", f"Failed to delete material: {e}")

    def _update_layer_material_dropdown(self):
        """Update the layer material dropdown to include custom prepregs."""
        if not hasattr(self, 'mat_combo'):
            return

        # Get predefined materials
        predefined = ["T300/5208 Carbon/Epoxy", "E-Glass/Epoxy", "S-Glass/Epoxy", "Kevlar-49/Epoxy"]

        # Add custom materials
        custom_names = []
        if self.project_manager.current_project and \
           self.project_manager.current_project.custom_prepreg_materials:
            custom_names = [f"[Custom] {m.name}" for m in self.project_manager.current_project.custom_prepreg_materials]

        # Combine
        all_materials = predefined + custom_names

        # Update dropdown
        try:
            self.mat_combo.configure(values=all_materials)
        except:
            pass  # Ignore if widget doesn't exist anymore

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

        # Get available materials for layers (predefined + custom)
        predefined_materials = ["T300/5208 Carbon/Epoxy", "E-Glass/Epoxy", "S-Glass/Epoxy", "Kevlar-49/Epoxy"]
        custom_materials = []
        if self.project_manager.current_project and \
           self.project_manager.current_project.custom_prepreg_materials:
            custom_materials = [f"[Custom] {m.name}" for m in self.project_manager.current_project.custom_prepreg_materials]

        layer_materials = predefined_materials + custom_materials
        self.layer_material_var = ctk.StringVar(value=layer_materials[0])
        self.mat_combo = ctk.CTkComboBox(
            mat_frame,
            variable=self.layer_material_var,
            values=layer_materials,
            width=250
        )
        self.mat_combo.pack(side="left", padx=(10, 0))

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

            # REMOVED: Thermal expansion processing - not used in flutter analysis
            alpha = None

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
                # Clear the form
                self.name_entry.delete(0, 'end')
                self.e_entry.delete(0, 'end')
                self.nu_entry.delete(0, 'end')
                self.g_entry.delete(0, 'end')
                self.rho_entry.delete(0, 'end')
            else:
                self.show_warning("Warning", "Please create a project first.\n\nClick 'Create Project' button at the top of this page.")

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
                self.show_warning("Warning", "Please create a project first.\n\nClick 'Create Project' button at the top of this page.")

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
        """Create or retrieve a layer material (predefined or custom)."""
        # Check if it's a custom material
        if name.startswith("[Custom] "):
            actual_name = name.replace("[Custom] ", "")
            if self.project_manager.current_project and \
               self.project_manager.current_project.custom_prepreg_materials:
                for custom_mat in self.project_manager.current_project.custom_prepreg_materials:
                    if custom_mat.name == actual_name:
                        return custom_mat

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
                self.show_warning("Warning", "Please create a project first.\n\nClick 'Create Project' button at the top of this page.")

        except Exception as e:
            self.show_error("Error", f"Failed to create laminate: {e}")

    def _show_sandwich_content(self):
        """Show honeycomb sandwich panel content."""
        self.current_material_type = MaterialType.SANDWICH
        self._clear_content_area()

        # Import sandwich materials
        from models.material import PredefinedMaterials, SandwichPanel

        # Main container
        main_frame = self.theme_manager.create_styled_frame(
            self.content_area,
            elevated=True
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Title
        title_label = self.theme_manager.create_styled_label(
            main_frame,
            text="Honeycomb Sandwich Panel Configuration",
            style="subheading"
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 10))

        # Predefined sandwich panels section
        predefined_frame = self.theme_manager.create_styled_frame(main_frame)
        predefined_frame.pack(fill="x", padx=20, pady=10)

        pred_label = self.theme_manager.create_styled_label(
            predefined_frame,
            text="Predefined Sandwich Panels:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        pred_label.pack(anchor="w", padx=15, pady=(15, 5))

        # Predefined options
        predefined_options = [
            ("Aluminum Sandwich (0.5\" core)", PredefinedMaterials.create_aluminum_sandwich),
            ("Composite Sandwich (0.75\" core)", PredefinedMaterials.create_composite_sandwich)
        ]

        for name, factory_func in predefined_options:
            btn_frame = ctk.CTkFrame(predefined_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=5)

            select_btn = ctk.CTkButton(
                btn_frame,
                text=f"Load: {name}",
                command=lambda f=factory_func: self._load_predefined_sandwich(f),
                width=400,
                height=35
            )
            select_btn.pack(side="left", padx=(0, 10))

        # Custom sandwich panel section
        custom_frame = self.theme_manager.create_styled_frame(main_frame)
        custom_frame.pack(fill="both", expand=True, padx=20, pady=10)

        custom_label = self.theme_manager.create_styled_label(
            custom_frame,
            text="Custom Sandwich Panel:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        custom_label.pack(anchor="w", padx=15, pady=(15, 10))

        # Configuration grid
        config_grid = ctk.CTkFrame(custom_frame, fg_color="transparent")
        config_grid.pack(fill="both", expand=True, padx=15, pady=10)

        # Panel name
        name_label = self.theme_manager.create_styled_label(config_grid, text="Panel Name:")
        name_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.sandwich_name_entry = self.theme_manager.create_styled_entry(
            config_grid,
            placeholder_text="e.g., Custom Aluminum Sandwich"
        )
        self.sandwich_name_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        # Face material selection
        face_mat_label = self.theme_manager.create_styled_label(config_grid, text="Face Material:")
        face_mat_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.face_material_var = ctk.StringVar(value="Aluminum 6061-T6")
        face_material_dropdown = ctk.CTkComboBox(
            config_grid,
            variable=self.face_material_var,
            values=["Aluminum 6061-T6", "Steel 4130", "Titanium Ti-6Al-4V"],
            width=300
        )
        face_material_dropdown.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # Face thickness
        face_thick_label = self.theme_manager.create_styled_label(config_grid, text="Face Thickness [mm]:")
        face_thick_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.face_thickness_entry = self.theme_manager.create_styled_entry(
            config_grid,
            placeholder_text="0.5"
        )
        self.face_thickness_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.face_thickness_entry.insert(0, "0.5")

        # Core material selection
        core_mat_label = self.theme_manager.create_styled_label(config_grid, text="Core Material:")
        core_mat_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)

        self.core_material_var = ctk.StringVar(value="Al 5052 Honeycomb 1/4\"-3.0")
        core_material_dropdown = ctk.CTkComboBox(
            config_grid,
            variable=self.core_material_var,
            values=[
                "Al 5052 Honeycomb 1/4\"-3.0",
                "Al 5056 Honeycomb 3/16\"-4.5",
                "Nomex Honeycomb 1/8\"-3.0"
            ],
            width=300
        )
        core_material_dropdown.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        # Core thickness
        core_thick_label = self.theme_manager.create_styled_label(config_grid, text="Core Thickness [mm]:")
        core_thick_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.core_thickness_entry = self.theme_manager.create_styled_entry(
            config_grid,
            placeholder_text="12.7"
        )
        self.core_thickness_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        self.core_thickness_entry.insert(0, "12.7")

        config_grid.grid_columnconfigure(1, weight=1)

        # Properties display
        props_frame = self.theme_manager.create_styled_frame(custom_frame)
        props_frame.pack(fill="x", padx=15, pady=10)

        props_title = self.theme_manager.create_styled_label(
            props_frame,
            text="Calculated Properties:",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        props_title.pack(anchor="w", padx=15, pady=(10, 5))

        self.sandwich_props_text = ctk.CTkTextbox(
            props_frame,
            height=120,
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.sandwich_props_text.pack(fill="x", padx=15, pady=(5, 15))
        self.sandwich_props_text.insert("1.0", "Configure panel and click 'Calculate Properties' to see equivalent properties...")

        # Buttons
        button_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(5, 15))

        calc_btn = ctk.CTkButton(
            button_frame,
            text="Calculate Properties",
            command=self._calculate_sandwich_properties,
            width=180,
            height=35
        )
        calc_btn.pack(side="left", padx=(0, 10))

        save_btn = self.theme_manager.create_styled_button(
            button_frame,
            text="💾 Save Sandwich Panel",
            command=self._save_sandwich_panel,
            style="primary",
            width=180,
            height=35
        )
        save_btn.pack(side="left")

    def _load_predefined_sandwich(self, factory_func):
        """Load a predefined sandwich panel."""
        try:
            sandwich = factory_func()

            # Update UI fields
            self.sandwich_name_entry.delete(0, 'end')
            self.sandwich_name_entry.insert(0, sandwich.name)

            self.face_material_var.set(sandwich.face_material.name)
            self.face_thickness_entry.delete(0, 'end')
            self.face_thickness_entry.insert(0, str(sandwich.face_thickness))

            self.core_material_var.set(sandwich.core_material.name)
            self.core_thickness_entry.delete(0, 'end')
            self.core_thickness_entry.insert(0, str(sandwich.core_thickness))

            # Calculate and display properties
            self._calculate_sandwich_properties()

            self.show_info("Loaded", f"Loaded predefined sandwich: {sandwich.name}")

        except Exception as e:
            self.show_error("Error", f"Failed to load predefined sandwich: {e}")

    def _calculate_sandwich_properties(self):
        """Calculate and display sandwich panel properties."""
        try:
            from models.material import (
                PredefinedMaterials, SandwichPanel,
                IsotropicMaterial, HoneycombCore
            )

            # Get face material
            face_name = self.face_material_var.get()
            if "6061" in face_name:
                face_mat = PredefinedMaterials.aluminum_6061()
            elif "4130" in face_name:
                face_mat = PredefinedMaterials.steel_4130()
            elif "Ti-6Al-4V" in face_name:
                face_mat = PredefinedMaterials.titanium_6al4v()
            else:
                face_mat = PredefinedMaterials.aluminum_6061()

            # Get core material
            core_name = self.core_material_var.get()
            if "5052" in core_name:
                core_mat = PredefinedMaterials.aluminum_honeycomb_5052()
            elif "5056" in core_name:
                core_mat = PredefinedMaterials.aluminum_honeycomb_5056()
            elif "Nomex" in core_name:
                core_mat = PredefinedMaterials.nomex_honeycomb()
            else:
                core_mat = PredefinedMaterials.aluminum_honeycomb_5052()

            # Get thicknesses
            face_thick = float(self.face_thickness_entry.get())
            core_thick = float(self.core_thickness_entry.get())

            # Create temporary sandwich
            temp_sandwich = SandwichPanel(
                id=1,
                name=self.sandwich_name_entry.get() or "Custom Sandwich",
                face_material=face_mat,
                face_thickness=face_thick,
                core_material=core_mat,
                core_thickness=core_thick
            )

            # Get properties
            props = temp_sandwich.get_equivalent_properties()

            # Display properties
            self.sandwich_props_text.delete("1.0", "end")
            prop_text = f"""Sandwich Panel Properties:
Total Thickness:       {temp_sandwich.total_thickness:.3f} mm
Mass per Area:         {props['mass_per_area']:.4f} kg/m²
Flexural Rigidity (D): {props['flexural_rigidity']:.3e} N·m
Effective E:           {props['effective_youngs_modulus']/1e9:.2f} GPa
Weight Saving:         {props['weight_saving']:.1f}%
Equiv. Solid Thick:    {props['equivalent_solid_thickness_m']*1000:.3f} mm

For 508×254 mm panel (estimated):
  First mode freq:     ~{491.85*(props['flexural_rigidity']/1753)**0.5 / (props['mass_per_area']/3.42)**0.5:.1f} Hz
"""
            self.sandwich_props_text.insert("1.0", prop_text)

        except ValueError as e:
            self.show_error("Error", "Please enter valid numeric values for thicknesses")
        except Exception as e:
            self.show_error("Error", f"Failed to calculate properties: {e}")

    def _save_sandwich_panel(self):
        """Save custom sandwich panel to project."""
        try:
            from models.material import (
                PredefinedMaterials, SandwichPanel
            )

            if not self.project_manager.current_project:
                self.show_warning("Warning", "Please create a project first.\n\nClick 'Create Project' button at the top of this page.")
                return

            # Get face material
            face_name = self.face_material_var.get()
            if "6061" in face_name:
                face_mat = PredefinedMaterials.aluminum_6061()
            elif "4130" in face_name:
                face_mat = PredefinedMaterials.steel_4130()
            elif "Ti-6Al-4V" in face_name:
                face_mat = PredefinedMaterials.titanium_6al4v()
            else:
                face_mat = PredefinedMaterials.aluminum_6061()

            # Get core material
            core_name = self.core_material_var.get()
            if "5052" in core_name:
                core_mat = PredefinedMaterials.aluminum_honeycomb_5052()
            elif "5056" in core_name:
                core_mat = PredefinedMaterials.aluminum_honeycomb_5056()
            elif "Nomex" in core_name:
                core_mat = PredefinedMaterials.nomex_honeycomb()
            else:
                core_mat = PredefinedMaterials.aluminum_honeycomb_5052()

            # Get thicknesses
            name = self.sandwich_name_entry.get() or "Custom Sandwich Panel"
            face_thick = float(self.face_thickness_entry.get())
            core_thick = float(self.core_thickness_entry.get())

            # Create sandwich panel
            sandwich = SandwichPanel(
                id=1,
                name=name,
                face_material=face_mat,
                face_thickness=face_thick,
                core_material=core_mat,
                core_thickness=core_thick,
                description=f"Custom sandwich: {face_thick}mm {face_name} + {core_thick}mm {core_name}"
            )

            # Save to project
            self.project_manager.current_project.material = sandwich
            self.main_window.update_status()

            props = sandwich.get_equivalent_properties()
            self.show_info("Success",
                          f"Saved sandwich panel: {name}\n\n"
                          f"Total thickness: {sandwich.total_thickness:.2f} mm\n"
                          f"Weight saving: {props['weight_saving']:.1f}%\n"
                          f"Mass: {props['mass_per_area']:.2f} kg/m²")

        except ValueError as e:
            self.show_error("Error", "Please enter valid numeric values")
        except Exception as e:
            self.show_error("Error", f"Failed to save sandwich panel: {e}")

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
        # Update project warning visibility
        if hasattr(self, '_update_project_warning_visibility'):
            self._update_project_warning_visibility()

    def refresh(self):
        """Refresh the material panel."""
        self.on_show()