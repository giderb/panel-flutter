"""Main application window for the NASTRAN Panel Flutter Analysis GUI."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Optional
import threading

from .theme_manager import ThemeManager
from .project_manager import ProjectManager, Project
from .panels.home_panel import HomePanel
from .panels.material_panel import MaterialPanel
from .panels.structural_panel import StructuralPanel
from .panels.aerodynamics_panel import AerodynamicsPanel
from .panels.analysis_panel import AnalysisPanel
from .panels.results_panel import ResultsPanel
from .panels.validation_panel import ValidationPanel
from utils.config import Config

class MainWindow:
    """Main application window."""

    def __init__(self, root: ctk.CTk, config: Config, theme_manager: ThemeManager,
                 project_manager: ProjectManager, logger):
        self.root = root
        self.config = config
        self.theme_manager = theme_manager
        self.project_manager = project_manager
        self.logger = logger

        self.current_panel = None
        self.panels = {}

        self._setup_window()
        self._create_menu()
        self._create_main_layout()
        self._create_panels()
        self._show_panel("home")

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_window(self):
        """Setup main window properties."""
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        self.root.geometry(f"1400x900+{x}+{y}")

        # Set window icon
        try:
            from pathlib import Path
            icon_path = Path(__file__).parent / "assets" / "app_icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
                self.logger.info(f"Window icon set successfully: {icon_path}")
            else:
                self.logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            self.logger.warning(f"Could not set window icon: {e}")

        # Apply theme
        appearance = self.config.get_appearance_settings()
        self.theme_manager.set_theme(appearance["theme"], appearance["color_theme"])

        # Set scaling
        ctk.set_widget_scaling(appearance["scaling"])

    def _create_menu(self):
        """Create application menu bar."""
        # Create menu bar (using tkinter for compatibility)
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self._new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project", command=self._open_project, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save Project", command=self._save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()

        # Recent projects submenu
        recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Projects", menu=recent_menu)
        self._update_recent_menu(recent_menu)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing, accelerator="Ctrl+Q")

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Validate Project", command=self._validate_project)
        analysis_menu.add_command(label="Run Analysis", command=self._run_analysis)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Export BDF", command=self._export_bdf)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)

        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Dark Mode", command=lambda: self._set_theme("dark"))
        theme_menu.add_command(label="Light Mode", command=lambda: self._set_theme("light"))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)

        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self._new_project())
        self.root.bind('<Control-o>', lambda e: self._open_project())
        self.root.bind('<Control-s>', lambda e: self._save_project())
        self.root.bind('<Control-Shift-S>', lambda e: self._save_project_as())
        self.root.bind('<Control-q>', lambda e: self._on_closing())

    def _create_main_layout(self):
        """Create the main layout with sidebar and content area."""
        # Main container
        self.main_container = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)

        # Create sidebar
        self._create_sidebar()

        # Create content area
        self.content_frame = self.theme_manager.create_styled_frame(
            self.main_container,
            corner_radius=0
        )
        self.content_frame.pack(side="right", fill="both", expand=True, padx=(0, 0), pady=0)

    def _create_sidebar(self):
        """Create navigation sidebar."""
        self.sidebar = self.theme_manager.create_styled_frame(
            self.main_container,
            elevated=True,
            corner_radius=0,
            width=200
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Logo/Title - Sleek modern design
        title_frame = self.theme_manager.create_styled_frame(self.sidebar, corner_radius=0)
        title_frame.pack(fill="x", padx=10, pady=(20, 30))

        # Icon with gradient-style design
        icon_label = ctk.CTkLabel(
            title_frame,
            text="✈️",
            font=self.theme_manager.get_display_font(),
            text_color=("#0066CC", "#00A8FF")  # Blue gradient effect
        )
        icon_label.pack(pady=(0, 5))

        # App name - modern minimal design
        title_label = ctk.CTkLabel(
            title_frame,
            text="Panel Flutter",
            font=self.theme_manager.get_title_font(),
            text_color=("#1a1a1a", "#ffffff")
        )
        title_label.pack(pady=(0, 2))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="NASTRAN Analysis",
            font=self.theme_manager.get_caption_font(),
            text_color=("#666666", "#999999")
        )
        subtitle_label.pack(pady=(0, 10))

        # Navigation buttons
        nav_items = [
            ("Home", "home", "🏠"),
            ("Material", "material", "🔧"),
            ("Structure", "structure", "🔲"),
            ("Aerodynamics", "aerodynamics", "💨"),
            ("Analysis", "analysis", "⚙️"),
            ("Results", "results", "📊"),
            ("Validation", "validation", "🔬")
        ]

        self.nav_buttons = {}
        for name, panel_id, icon in nav_items:
            btn = self._create_nav_button(name, panel_id, icon)
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[panel_id] = btn

        # Status area at bottom
        self._create_status_area()

    def _create_nav_button(self, text: str, panel_id: str, icon: str) -> ctk.CTkButton:
        """Create a navigation button."""
        def nav_command():
            self._show_panel(panel_id)

        btn = ctk.CTkButton(
            self.sidebar,
            text=f"{icon}  {text}",
            command=nav_command,
            anchor="w",
            height=40,
            font=self.theme_manager.get_body_large_font(),
            fg_color="transparent",
            text_color=self.theme_manager.get_color("text"),
            hover_color=self.theme_manager.get_color("primary")
        )
        return btn

    def _create_status_area(self):
        """Create status area in sidebar."""
        # Status frame - pack at bottom with no spacer
        status_frame = self.theme_manager.create_styled_frame(
            self.sidebar,
            elevated=False,  # Match sidebar background
            corner_radius=0
        )
        status_frame.pack(side="bottom", fill="x", padx=0, pady=10)

        # Project status
        self.status_label = self.theme_manager.create_styled_label(
            status_frame,
            text="No project loaded",
            style="caption",
            font=self.theme_manager.get_caption_font()
        )
        self.status_label.pack(pady=(10, 5))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            status_frame,
            height=4,
            progress_color=self.theme_manager.get_color("accent")
        )
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)

    def _create_panels(self):
        """Create all application panels."""
        self.panels = {
            "home": HomePanel(self.content_frame, self),
            "material": MaterialPanel(self.content_frame, self),
            "structure": StructuralPanel(self.content_frame, self),
            "aerodynamics": AerodynamicsPanel(self.content_frame, self),
            "analysis": AnalysisPanel(self.content_frame, self),
            "results": ResultsPanel(self.content_frame, self),
            "validation": ValidationPanel(self.content_frame, self)
        }

    def _show_panel(self, panel_id: str):
        """Show the specified panel."""
        if self.current_panel:
            self.current_panel.hide()

        if panel_id in self.panels:
            self.current_panel = self.panels[panel_id]
            self.current_panel.show()

            # Update navigation button states
            for btn_id, btn in self.nav_buttons.items():
                if btn_id == panel_id:
                    btn.configure(
                        fg_color=self.theme_manager.get_color("primary"),
                        text_color="#ffffff"
                    )
                else:
                    btn.configure(
                        fg_color="transparent",
                        text_color=self.theme_manager.get_color("text")
                    )

    def update_status(self, message: str = None, progress: float = None):
        """Update status display."""
        if message:
            self.status_label.configure(text=message)

        if progress is not None:
            self.progress_bar.set(progress)

        # Update based on current project
        if self.project_manager.current_project:
            project = self.project_manager.current_project
            completion = project.get_completion_percentage()
            if not message:
                self.status_label.configure(text=f"Project: {project.name}")
            if progress is None:
                self.progress_bar.set(completion / 100.0)

    # Menu command implementations
    def _new_project(self):
        """Create a new project."""
        if self.panels and "home" in self.panels:
            self.panels["home"].show_new_project_dialog()

    def _open_project(self):
        """Open an existing project."""
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json"
        )

        if file_path:
            project = self.project_manager.load_project(file_path)
            if project:
                self.update_status(f"Opened project: {project.name}")
                self._refresh_panels()
                messagebox.showinfo("Success", f"Project '{project.name}' loaded successfully.")
            else:
                messagebox.showerror("Error", "Failed to load project file.")

    def _save_project(self):
        """Save current project."""
        if not self.project_manager.current_project:
            messagebox.showwarning("Warning", "No project to save.")
            return

        if self.project_manager.save_project():
            project = self.project_manager.current_project
            self.update_status(f"Saved project: {project.name}")
            messagebox.showinfo("Success", f"Project '{project.name}' saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save project.")

    def _save_project_as(self):
        """Save current project with a new name."""
        if not self.project_manager.current_project:
            messagebox.showwarning("Warning", "No project to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json"
        )

        if file_path:
            # Implementation for save as
            messagebox.showinfo("Info", "Save As functionality not yet implemented.")

    def _update_recent_menu(self, menu):
        """Update recent projects menu."""
        # Clear existing items
        menu.delete(0, 'end')

        recent_projects = self.project_manager.get_recent_projects()
        if not recent_projects:
            menu.add_command(label="(No recent projects)", state="disabled")
            return

        for project in recent_projects:
            menu.add_command(
                label=f"{project.name} ({project.modified_at.strftime('%Y-%m-%d')})",
                command=lambda p=project: self._load_recent_project(p)
            )

    def _load_recent_project(self, project: Project):
        """Load a recent project."""
        project_file = self.project_manager.projects_dir / f"{project.id}.json"
        if project_file.exists():
            self.project_manager.current_project = project
            self._refresh_panels()
            self.update_status(f"Loaded project: {project.name}")
        else:
            messagebox.showerror("Error", f"Project file not found: {project_file}")

    def _validate_project(self):
        """Validate current project."""
        if not self.project_manager.current_project:
            messagebox.showwarning("Warning", "No project to validate.")
            return

        errors = self.project_manager.current_project.validate()
        if not errors:
            messagebox.showinfo("Validation", "Project configuration is valid!")
        else:
            error_message = "Project validation errors:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showwarning("Validation Errors", error_message)

    def _run_analysis(self):
        """Run NASTRAN analysis."""
        self._show_panel("analysis")
        if "analysis" in self.panels:
            self.panels["analysis"].run_analysis()

    def _export_bdf(self):
        """Export BDF file."""
        messagebox.showinfo("Info", "BDF export functionality will be available in the Analysis panel.")

    def _set_theme(self, theme: str):
        """Set application theme."""
        self.theme_manager.set_theme(theme)
        self.config.set("appearance.theme", theme)
        self.config.save()
        messagebox.showinfo("Theme", f"Theme changed to {theme}. Restart application for full effect.")

    def _show_help(self):
        """Show help dialog."""
        help_text = """
NASTRAN Panel Flutter Analysis GUI

This application provides a comprehensive interface for supersonic panel flutter analysis.

Workflow Steps:
1. Material: Define material properties (isotropic, orthotropic, or composite)
2. Geometry: Set plate dimensions and mesh parameters
3. Aerodynamics: Configure flow conditions and aerodynamic theory
4. Analysis: Run NASTRAN analysis
5. Results: View V-f and V-g plots, critical flutter points

For detailed help, please refer to the README.md file.
        """
        messagebox.showinfo("Help", help_text)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
✈️ Panel Flutter - NASTRAN Analysis
Version 1.0.0

A modern, sleek interface for supersonic panel flutter analysis
using NASTRAN and advanced aeroelastic methods.

Built with customtkinter for a professional, modern appearance.

© 2024 - Built for aerospace engineering research and analysis.
        """
        messagebox.showinfo("About", about_text)

    def _refresh_panels(self):
        """Refresh all panels with current project data."""
        for panel in self.panels.values():
            if hasattr(panel, 'refresh'):
                panel.refresh()

    def _on_closing(self):
        """Handle window close event."""
        if self.project_manager.current_project:
            result = messagebox.askyesnocancel(
                "Save Project",
                "Do you want to save your current project before exiting?"
            )
            if result is True:  # Yes
                self._save_project()
            elif result is None:  # Cancel
                return

        self.logger.info("Application closing")
        self.root.quit()
        self.root.destroy()