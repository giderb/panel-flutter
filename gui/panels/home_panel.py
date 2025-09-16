"""Home panel - project overview and management."""

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from typing import Optional
from datetime import datetime

from .base_panel import BasePanel
from ..project_manager import Project
from models.material import PredefinedMaterials

class HomePanel(BasePanel):
    """Home panel showing project overview and management."""

    def _setup_ui(self):
        """Setup the home panel UI."""
        # Main scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.frame,
            corner_radius=0,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Welcome section
        self._create_welcome_section()

        # Current project section
        self._create_current_project_section()

        # Recent projects section
        self._create_recent_projects_section()

        # Quick start section
        self._create_quick_start_section()

    def _create_welcome_section(self):
        """Create the welcome section."""
        welcome_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        welcome_frame.pack(fill="x", pady=(0, 20))

        # Title and description
        title_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=20)

        title_label = self.theme_manager.create_styled_label(
            title_frame,
            text="NASTRAN Panel Flutter Analysis",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")

        subtitle_label = self.theme_manager.create_styled_label(
            title_frame,
            text="Modern GUI for supersonic panel flutter analysis using NASTRAN",
            font=ctk.CTkFont(size=14),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # Action buttons
        buttons_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

        new_btn = self.theme_manager.create_styled_button(
            buttons_frame,
            text="📝 New Project",
            command=self.show_new_project_dialog,
            style="primary",
            width=150,
            height=40
        )
        new_btn.pack(side="left", padx=(0, 10))

        open_btn = self.theme_manager.create_styled_button(
            buttons_frame,
            text="📁 Open Project",
            command=self._open_project,
            style="secondary",
            width=150,
            height=40
        )
        open_btn.pack(side="left", padx=(0, 10))

        examples_btn = self.theme_manager.create_styled_button(
            buttons_frame,
            text="🚀 Load Example",
            command=self._show_examples,
            style="secondary",
            width=150,
            height=40
        )
        examples_btn.pack(side="left")

    def _create_current_project_section(self):
        """Create current project section."""
        self.project_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        self.project_frame.pack(fill="x", pady=(0, 20))

        self.project_header = self.theme_manager.create_styled_label(
            self.project_frame,
            text="Current Project",
            style="subheading"
        )
        self.project_header.pack(anchor="w", padx=20, pady=(20, 10))

        self.project_content = ctk.CTkFrame(self.project_frame, fg_color="transparent")
        self.project_content.pack(fill="x", padx=20, pady=(0, 20))

        self._update_project_display()

    def _create_recent_projects_section(self):
        """Create recent projects section."""
        recent_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        recent_frame.pack(fill="x", pady=(0, 20))

        recent_header = self.theme_manager.create_styled_label(
            recent_frame,
            text="Recent Projects",
            style="subheading"
        )
        recent_header.pack(anchor="w", padx=20, pady=(20, 10))

        self.recent_content = ctk.CTkFrame(recent_frame, fg_color="transparent")
        self.recent_content.pack(fill="x", padx=20, pady=(0, 20))

        self._update_recent_projects_display()

    def _create_quick_start_section(self):
        """Create quick start guide section."""
        quick_start_frame = self.theme_manager.create_styled_frame(
            self.scroll_frame,
            elevated=True
        )
        quick_start_frame.pack(fill="x", pady=(0, 20))

        header = self.theme_manager.create_styled_label(
            quick_start_frame,
            text="Quick Start Guide",
            style="subheading"
        )
        header.pack(anchor="w", padx=20, pady=(20, 10))

        steps = [
            ("1. Material Properties", "Define isotropic, orthotropic, or composite materials"),
            ("2. Geometry Setup", "Configure plate dimensions, thickness, and mesh"),
            ("3. Boundary Conditions", "Set edge constraints (SSSS, CCCC, etc.)"),
            ("4. Aerodynamic Configuration", "Choose theory and set flow conditions"),
            ("5. Analysis Parameters", "Configure modal and flutter analysis settings"),
            ("6. Run Analysis", "Execute NASTRAN analysis with progress monitoring"),
            ("7. View Results", "Analyze V-f diagrams and critical flutter points")
        ]

        for step_title, step_desc in steps:
            step_frame = ctk.CTkFrame(quick_start_frame, fg_color="transparent")
            step_frame.pack(fill="x", padx=20, pady=2)

            step_label = self.theme_manager.create_styled_label(
                step_frame,
                text=step_title,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            step_label.pack(anchor="w")

            desc_label = self.theme_manager.create_styled_label(
                step_frame,
                text=step_desc,
                font=ctk.CTkFont(size=11),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            desc_label.pack(anchor="w", padx=(20, 0), pady=(0, 5))

    def show_new_project_dialog(self):
        """Show new project creation dialog."""
        dialog = NewProjectDialog(self.frame, self.theme_manager)
        self.frame.wait_window(dialog.dialog)

        if dialog.result:
            name, description = dialog.result
            project = self.project_manager.create_project(name, description)
            self.main_window.update_status(f"Created project: {name}")
            self._update_project_display()
            self._update_recent_projects_display()
            self.show_info("Success", f"Project '{name}' created successfully!")

    def _open_project(self):
        """Open existing project."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            project = self.project_manager.load_project(file_path)
            if project:
                self.main_window.update_status(f"Opened: {project.name}")
                self._update_project_display()
                self._update_recent_projects_display()
                self.show_info("Success", f"Project '{project.name}' loaded!")
            else:
                self.show_error("Error", "Failed to load project file.")

    def _show_examples(self):
        """Show example projects dialog."""
        examples = [
            ("Metallic Panel", "Aluminum panel flutter analysis (from notebook)"),
            ("Composite Panel", "Carbon fiber panel with thermal effects"),
            ("Hypersonic Panel", "High-speed panel with thermal loading")
        ]

        dialog = ExampleSelectionDialog(self.frame, self.theme_manager, examples)
        self.frame.wait_window(dialog.dialog)

        if dialog.result:
            example_name = dialog.result
            self._create_example_project(example_name)

    def _create_example_project(self, example_name: str):
        """Create an example project."""
        if example_name == "Metallic Panel":
            project = self.project_manager.create_project(
                "Metallic Panel Example",
                "Aluminum panel flutter analysis based on nastran-aeroelasticity example"
            )

            # Set aluminum material
            aluminum = PredefinedMaterials.aluminum_6061()
            project.material = aluminum

            # Set geometry (matching notebook example)
            project.geometry = {
                "length": 300.0,  # mm
                "width": 300.0,   # mm
                "thickness": 1.5, # mm
                "n_chord": 20,
                "n_span": 20
            }

            # Set boundary conditions
            project.boundary_conditions = "SSSS"  # Simply supported

            # Set aerodynamic configuration
            project.aerodynamic_config = {
                "theory": "piston",
                "flow_conditions": {
                    "mach_numbers": [3.0],
                    "velocities": list(range(822000, 1066000, 5000)),  # mm/s
                    "reference_velocity": 1000.0,
                    "reference_density": 1.225e-12,  # ton/mm³
                    "reference_chord": 300.0,
                    "alphas": [0.0, 0.0, 0.0, 0.0],
                    "density_ratios": [0.5],
                    "reduced_frequencies": [0.001, 0.1, 0.2, 0.4]
                }
            }

            # Set analysis parameters
            project.analysis_params = {
                "n_modes": 15,
                "frequency_limits": [0.0, 1000.0],
                "method": "PK",
                "nastran_params": {
                    "VREF": 1000.0,
                    "COUPMASS": 1,
                    "LMODES": 15,
                    "WTMASS": 1.0,
                    "GRDPNT": 1,
                    "OPPHIPA": 1
                }
            }

            self.project_manager.save_project(project)
            self.main_window.update_status(f"Created example: {example_name}")
            self._update_project_display()
            self._update_recent_projects_display()
            self.show_info("Success", f"Example project '{example_name}' created!")

        else:
            self.show_info("Info", f"Example '{example_name}' will be available in a future update.")

    def _update_project_display(self):
        """Update current project display."""
        # Clear existing content
        for widget in self.project_content.winfo_children():
            widget.destroy()

        project = self.project_manager.current_project

        if not project:
            no_project_label = self.theme_manager.create_styled_label(
                self.project_content,
                text="No project loaded. Create a new project or open an existing one.",
                text_color=self.theme_manager.get_color("text_secondary")
            )
            no_project_label.pack(anchor="w")
            return

        # Project info
        info_frame = ctk.CTkFrame(self.project_content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))

        name_label = self.theme_manager.create_styled_label(
            info_frame,
            text=project.name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(anchor="w")

        if project.description:
            desc_label = self.theme_manager.create_styled_label(
                info_frame,
                text=project.description,
                text_color=self.theme_manager.get_color("text_secondary")
            )
            desc_label.pack(anchor="w")

        # Project status
        status_frame = ctk.CTkFrame(self.project_content, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 10))

        completion = project.get_completion_percentage()
        status_label = self.theme_manager.create_styled_label(
            status_frame,
            text=f"Completion: {completion:.0f}%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        status_label.pack(anchor="w")

        progress_bar = ctk.CTkProgressBar(status_frame)
        progress_bar.pack(fill="x", pady=(5, 0))
        progress_bar.set(completion / 100.0)

        # Component status
        components = [
            ("Material", project.material is not None),
            ("Geometry", project.geometry is not None),
            ("Boundary Conditions", project.boundary_conditions is not None),
            ("Aerodynamics", project.aerodynamic_config is not None),
            ("Analysis Params", project.analysis_params is not None),
            ("Thermal", project.thermal_conditions is not None)
        ]

        components_frame = ctk.CTkFrame(self.project_content, fg_color="transparent")
        components_frame.pack(fill="x")

        for i, (name, configured) in enumerate(components):
            if i % 3 == 0:
                row_frame = ctk.CTkFrame(components_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

            status_icon = "✅" if configured else "❌"
            comp_label = self.theme_manager.create_styled_label(
                row_frame,
                text=f"{status_icon} {name}",
                font=ctk.CTkFont(size=11)
            )
            comp_label.pack(side="left", padx=(0, 20))

    def _update_recent_projects_display(self):
        """Update recent projects display."""
        # Clear existing content
        for widget in self.recent_content.winfo_children():
            widget.destroy()

        recent_projects = self.project_manager.get_recent_projects()

        if not recent_projects:
            no_recent_label = self.theme_manager.create_styled_label(
                self.recent_content,
                text="No recent projects.",
                text_color=self.theme_manager.get_color("text_secondary")
            )
            no_recent_label.pack(anchor="w")
            return

        for project in recent_projects[:5]:  # Show only 5 most recent
            project_frame = ctk.CTkFrame(
                self.recent_content,
                fg_color=self.theme_manager.get_color("surface"),
                corner_radius=8
            )
            project_frame.pack(fill="x", pady=2)

            # Project info
            info_frame = ctk.CTkFrame(project_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

            name_label = self.theme_manager.create_styled_label(
                info_frame,
                text=project.name,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            name_label.pack(anchor="w")

            date_label = self.theme_manager.create_styled_label(
                info_frame,
                text=f"Modified: {project.modified_at.strftime('%Y-%m-%d %H:%M')}",
                font=ctk.CTkFont(size=10),
                text_color=self.theme_manager.get_color("text_secondary")
            )
            date_label.pack(anchor="w")

            # Load button
            load_btn = self.theme_manager.create_styled_button(
                project_frame,
                text="Load",
                command=lambda p=project: self._load_recent_project(p),
                style="secondary",
                width=80,
                height=30
            )
            load_btn.pack(side="right", padx=10, pady=10)

    def _load_recent_project(self, project: Project):
        """Load a recent project."""
        self.project_manager.current_project = project
        self.main_window.update_status(f"Loaded: {project.name}")
        self._update_project_display()

    def on_show(self):
        """Called when panel is shown."""
        self._update_project_display()
        self._update_recent_projects_display()
        self.main_window.update_status()

    def refresh(self):
        """Refresh the home panel."""
        self.on_show()


class NewProjectDialog:
    """Dialog for creating a new project."""

    def __init__(self, parent, theme_manager):
        self.theme_manager = theme_manager
        self.result = None

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("New Project")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 150
        self.dialog.geometry(f"400x300+{x}+{y}")

        self._create_dialog_ui()

    def _create_dialog_ui(self):
        """Create dialog UI."""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Create New Project",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Project name
        name_label = ctk.CTkLabel(main_frame, text="Project Name:")
        name_label.pack(anchor="w", pady=(0, 5))

        self.name_entry = ctk.CTkEntry(main_frame, width=350, height=35)
        self.name_entry.pack(pady=(0, 15))
        self.name_entry.focus()

        # Description
        desc_label = ctk.CTkLabel(main_frame, text="Description (Optional):")
        desc_label.pack(anchor="w", pady=(0, 5))

        self.desc_text = ctk.CTkTextbox(main_frame, width=350, height=100)
        self.desc_text.pack(pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="transparent",
            border_width=2,
            width=100
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        create_btn = ctk.CTkButton(
            button_frame,
            text="Create",
            command=self._create,
            width=100
        )
        create_btn.pack(side="right")

        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self._create())
        self.dialog.bind('<Escape>', lambda e: self._cancel())

    def _create(self):
        """Create project and close dialog."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a project name.")
            return

        description = self.desc_text.get("1.0", "end").strip()
        self.result = (name, description if description else "")
        self.dialog.destroy()

    def _cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()


class ExampleSelectionDialog:
    """Dialog for selecting example projects."""

    def __init__(self, parent, theme_manager, examples):
        self.theme_manager = theme_manager
        self.examples = examples
        self.result = None

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Load Example Project")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 200
        self.dialog.geometry(f"500x400+{x}+{y}")

        self._create_dialog_ui()

    def _create_dialog_ui(self):
        """Create dialog UI."""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Select Example Project",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Examples list
        for name, description in self.examples:
            example_frame = ctk.CTkFrame(main_frame)
            example_frame.pack(fill="x", pady=5)

            info_frame = ctk.CTkFrame(example_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

            name_label = ctk.CTkLabel(
                info_frame,
                text=name,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            name_label.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                info_frame,
                text=description,
                font=ctk.CTkFont(size=11)
            )
            desc_label.pack(anchor="w")

            load_btn = ctk.CTkButton(
                example_frame,
                text="Load",
                command=lambda n=name: self._load_example(n),
                width=80
            )
            load_btn.pack(side="right", padx=15, pady=15)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            main_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="transparent",
            border_width=2,
            width=100
        )
        cancel_btn.pack(pady=(20, 0))

    def _load_example(self, name: str):
        """Load selected example."""
        self.result = name
        self.dialog.destroy()

    def _cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()