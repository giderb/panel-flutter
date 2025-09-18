"""Real flutter analysis execution panel."""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict, Any
import threading
import json
from pathlib import Path

from .base_panel import BasePanel
from python_bridge.analysis_executor import executor
from utils.nastran_detector import find_nastran_executables, get_default_nastran_path
from utils.config import Config


class AnalysisPanel(BasePanel):
    """Panel for executing real flutter analysis."""

    def __init__(self, parent, main_window):
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.analysis_running = False
        self.config = Config()
        self.nastran_paths = []
        super().__init__(parent, main_window)

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        # Create main content area
        content_frame = self.theme_manager.create_styled_frame(self.frame, elevated=True)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(3, weight=1)  # Results display row

        # Title
        title_label = self.theme_manager.create_styled_label(
            content_frame,
            text="Flutter Analysis Execution",
            style="heading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # NASTRAN settings
        self._setup_nastran_settings(content_frame)

        # Analysis configuration
        self._setup_analysis_config(content_frame)

        # Results display
        self._setup_results_display(content_frame)

        # Control buttons
        self._setup_control_buttons(content_frame)

    def _setup_nastran_settings(self, parent):
        """Setup NASTRAN solver settings section."""
        nastran_frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        nastran_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        nastran_frame.grid_columnconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            nastran_frame,
            text="NASTRAN Solver Settings",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        # NASTRAN executable path
        path_label = self.theme_manager.create_styled_label(nastran_frame, text="NASTRAN Executable:")
        path_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        # Auto-detect paths in background thread
        self.nastran_path_var = ctk.StringVar(value=self.config.get_nastran_executable())
        self.nastran_combo = ctk.CTkComboBox(
            nastran_frame,
            variable=self.nastran_path_var,
            values=["nastran (from PATH)"]
        )
        self.nastran_combo.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=5)

        # Browse button
        browse_button = self.theme_manager.create_styled_button(
            nastran_frame,
            text="📁 Browse",
            style="secondary",
            command=self._browse_nastran_path
        )
        browse_button.grid(row=1, column=2, padx=(0, 20), pady=5)

        # Auto-detect button
        detect_button = self.theme_manager.create_styled_button(
            nastran_frame,
            text="🔍 Auto-Detect",
            style="secondary",
            command=self._auto_detect_nastran
        )
        detect_button.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=(5, 15))

        # Status label
        self.nastran_status_label = self.theme_manager.create_styled_label(
            nastran_frame,
            text="Status: Ready",
            style="caption"
        )
        self.nastran_status_label.grid(row=2, column=2, sticky="w", padx=(0, 20), pady=(5, 15))

        # Start auto-detection
        threading.Thread(target=self._detect_nastran_background, daemon=True).start()

    def _setup_analysis_config(self, parent):
        """Setup analysis configuration section."""
        config_frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        config_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        config_frame.grid_columnconfigure((1, 3), weight=1)

        title_label = self.theme_manager.create_styled_label(
            config_frame,
            text="Analysis Configuration",
            style="subheading"
        )
        title_label.grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 10))

        # Analysis method
        method_label = self.theme_manager.create_styled_label(config_frame, text="Method:")
        method_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=5)

        self.method_var = ctk.StringVar(value="auto")
        method_combo = ctk.CTkComboBox(
            config_frame,
            variable=self.method_var,
            values=["auto", "piston_theory", "doublet_lattice", "nastran", "multi_solver"]
        )
        method_combo.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Velocity range
        v_min_label = self.theme_manager.create_styled_label(config_frame, text="Min Velocity [m/s]:")
        v_min_label.grid(row=1, column=2, sticky="w", padx=(20, 10), pady=5)

        self.v_min_var = ctk.StringVar(value="50")
        v_min_entry = self.theme_manager.create_styled_entry(
            config_frame,
            textvariable=self.v_min_var,
            placeholder_text="Minimum velocity"
        )
        v_min_entry.grid(row=1, column=3, sticky="ew", padx=(0, 20), pady=5)

        # Max velocity
        v_max_label = self.theme_manager.create_styled_label(config_frame, text="Max Velocity [m/s]:")
        v_max_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=5)

        self.v_max_var = ctk.StringVar(value="1000")
        v_max_entry = self.theme_manager.create_styled_entry(
            config_frame,
            textvariable=self.v_max_var,
            placeholder_text="Maximum velocity"
        )
        v_max_entry.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=5)

        # Number of points
        points_label = self.theme_manager.create_styled_label(config_frame, text="Velocity Points:")
        points_label.grid(row=2, column=2, sticky="w", padx=(20, 10), pady=5)

        self.points_var = ctk.StringVar(value="20")
        points_entry = self.theme_manager.create_styled_entry(
            config_frame,
            textvariable=self.points_var,
            placeholder_text="Number of points"
        )
        points_entry.grid(row=2, column=3, sticky="ew", padx=(0, 20), pady=(5, 15))

    def _setup_results_display(self, parent):
        """Setup results display section."""
        results_frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        results_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        title_label = self.theme_manager.create_styled_label(
            results_frame,
            text="Analysis Results",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        # Create notebook for results
        self.results_notebook = ctk.CTkTabview(results_frame)
        self.results_notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))

        # Add tabs
        self.summary_tab = self.results_notebook.add("Summary")
        self.detailed_tab = self.results_notebook.add("Detailed Results")
        self.bdf_tab = self.results_notebook.add("BDF Export")

        self._setup_summary_tab()
        self._setup_detailed_tab()
        self._setup_bdf_tab()

    def _setup_summary_tab(self):
        """Setup summary results tab."""
        self.summary_tab.grid_columnconfigure(0, weight=1)

        # Critical results
        critical_frame = self.theme_manager.create_styled_frame(self.summary_tab, elevated=True)
        critical_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        critical_frame.grid_columnconfigure((0, 1), weight=1)

        critical_title = self.theme_manager.create_styled_label(
            critical_frame,
            text="Critical Flutter Results",
            style="subheading"
        )
        critical_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Flutter speed
        speed_frame = ctk.CTkFrame(critical_frame, fg_color="blue", corner_radius=8)
        speed_frame.grid(row=1, column=0, sticky="ew", padx=(20, 10), pady=5)

        self.flutter_speed_label = self.theme_manager.create_styled_label(
            speed_frame,
            text="Flutter Speed\n-- m/s",
            text_color="white",
            font=("Segoe UI", 14, "bold")
        )
        self.flutter_speed_label.pack(padx=15, pady=15)

        # Flutter frequency
        freq_frame = ctk.CTkFrame(critical_frame, fg_color="green", corner_radius=8)
        freq_frame.grid(row=1, column=1, sticky="ew", padx=(10, 20), pady=5)

        self.flutter_freq_label = self.theme_manager.create_styled_label(
            freq_frame,
            text="Flutter Frequency\n-- Hz",
            text_color="white",
            font=("Segoe UI", 14, "bold")
        )
        self.flutter_freq_label.pack(padx=15, pady=15)

        # Analysis method
        self.method_result_label = self.theme_manager.create_styled_label(
            critical_frame,
            text="Analysis Method: Not Run",
            style="caption"
        )
        self.method_result_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 15))

    def _setup_detailed_tab(self):
        """Setup detailed results tab."""
        self.detailed_tab.grid_columnconfigure(0, weight=1)
        self.detailed_tab.grid_rowconfigure(0, weight=1)

        # Results text area
        self.detailed_text = ctk.CTkTextbox(
            self.detailed_tab,
            wrap="word",
            font=("Courier", 10)
        )
        self.detailed_text.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def _setup_bdf_tab(self):
        """Setup BDF export tab."""
        self.bdf_tab.grid_columnconfigure(0, weight=1)
        self.bdf_tab.grid_rowconfigure(1, weight=1)

        # BDF info
        info_frame = self.theme_manager.create_styled_frame(self.bdf_tab, elevated=True)
        info_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        info_title = self.theme_manager.create_styled_label(
            info_frame,
            text="NASTRAN BDF File Generation",
            style="subheading"
        )
        info_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        info_text = ("Generate NASTRAN Bulk Data File (BDF) for external analysis. "
                    "The BDF file contains all structural and aerodynamic model definitions.")
        info_label = self.theme_manager.create_styled_label(
            info_frame,
            text=info_text,
            style="caption",
            wraplength=600
        )
        info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

        # BDF generation button
        self.generate_bdf_button = self.theme_manager.create_styled_button(
            info_frame,
            text="📄 Generate BDF File",
            style="secondary",
            command=self._generate_bdf
        )
        self.generate_bdf_button.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 15))

        # BDF preview
        self.bdf_text = ctk.CTkTextbox(
            self.bdf_tab,
            wrap="none",
            font=("Courier", 9)
        )
        self.bdf_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_control_buttons(self, parent):
        """Setup control buttons."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Run analysis button
        self.run_button = self.theme_manager.create_styled_button(
            button_frame,
            text="🚀 Run Flutter Analysis",
            style="primary",
            command=self._run_analysis
        )
        self.run_button.pack(side="left", padx=(0, 10))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(button_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(10, 10))
        self.progress_bar.set(0)

        # Progress label
        self.progress_label = self.theme_manager.create_styled_label(
            button_frame,
            text="Ready to run analysis",
            style="caption"
        )
        self.progress_label.pack(side="right", padx=(10, 0))

        # Export results button
        self.export_button = self.theme_manager.create_styled_button(
            button_frame,
            text="💾 Export Results",
            style="secondary",
            command=self._export_results,
            state="disabled"
        )
        self.export_button.pack(side="right", padx=(10, 0))

    def _detect_nastran_background(self):
        """Auto-detect NASTRAN executables in background thread."""
        try:
            self.main_window.root.after(0, lambda: self.nastran_status_label.configure(text="Status: Detecting..."))

            # Find NASTRAN executables
            self.nastran_paths = find_nastran_executables()

            # Update combo box values
            if self.nastran_paths:
                values = []
                for path in self.nastran_paths:
                    # Show short name for display
                    if len(path) > 60:
                        display_name = f"...{path[-57:]}"
                    else:
                        display_name = path
                    values.append(display_name)

                # Add manual option
                values.append("Custom path...")

                def update_combo():
                    self.nastran_combo.configure(values=values)
                    if self.nastran_paths:
                        # Set to first detected path if current is default
                        if self.nastran_path_var.get() == "nastran":
                            self.nastran_path_var.set(values[0])
                    self.nastran_status_label.configure(text=f"Status: Found {len(self.nastran_paths)} executable(s)")

                self.main_window.root.after(0, update_combo)
            else:
                def update_not_found():
                    self.nastran_combo.configure(values=["nastran (from PATH)", "Custom path..."])
                    self.nastran_status_label.configure(text="Status: No executables found")

                self.main_window.root.after(0, update_not_found)

        except Exception as e:
            def show_error():
                self.nastran_status_label.configure(text="Status: Detection failed")

            self.main_window.root.after(0, show_error)

    def _auto_detect_nastran(self):
        """Manually trigger NASTRAN auto-detection."""
        threading.Thread(target=self._detect_nastran_background, daemon=True).start()

    def _browse_nastran_path(self):
        """Browse for NASTRAN executable."""
        file_types = [("Executable files", "*.exe"), ("All files", "*.*")]

        file_path = filedialog.askopenfilename(
            title="Select NASTRAN Executable",
            filetypes=file_types
        )

        if file_path:
            # Add to combo box if not already there
            current_values = list(self.nastran_combo.cget("values"))

            # Remove "Custom path..." temporarily
            if "Custom path..." in current_values:
                current_values.remove("Custom path...")

            # Add new path
            if file_path not in current_values:
                current_values.append(file_path)
                self.nastran_paths.append(file_path)

            # Re-add custom option
            current_values.append("Custom path...")

            self.nastran_combo.configure(values=current_values)
            self.nastran_path_var.set(file_path)

            # Update config
            self.config.set("nastran.executable", file_path)
            self.config.save()

            self.nastran_status_label.configure(text="Status: Custom path set")

    def _get_current_nastran_path(self) -> str:
        """Get the currently selected NASTRAN path."""
        selected = self.nastran_path_var.get()

        # Handle display names vs actual paths
        if selected in self.nastran_paths:
            return selected

        # Find actual path from display name
        for i, path in enumerate(self.nastran_paths):
            display_name = path if len(path) <= 60 else f"...{path[-57:]}"
            if selected == display_name:
                return path

        # Fallback
        if selected == "nastran (from PATH)" or not selected:
            return "nastran"

        return selected

    def _run_analysis(self):
        """Run flutter analysis."""
        # Check if models are available
        if not self._validate_models():
            return

        self.analysis_running = True
        self.run_button.configure(state="disabled", text="Running Analysis...")
        self.progress_bar.set(0)

        # Start analysis in separate thread
        thread = threading.Thread(target=self._analysis_thread)
        thread.daemon = True
        thread.start()

    def _validate_models(self) -> bool:
        """Validate that required models are available."""
        if not hasattr(self.project_manager, 'current_project') or not self.project_manager.current_project:
            messagebox.showerror("Error", "No active project. Create a project first.")
            return False

        project = self.project_manager.current_project

        if not hasattr(project, 'structural_model') or not project.structural_model:
            messagebox.showerror("Error", "Structural model not defined. Complete the Structure tab first.")
            return False

        if not hasattr(project, 'aerodynamic_model') or not project.aerodynamic_model:
            messagebox.showerror("Error", "Aerodynamic model not defined. Complete the Aerodynamics tab first.")
            return False

        # Check if models are generated
        if not project.structural_model._mesh_generated:
            messagebox.showerror("Error", "Structural mesh not generated. Generate mesh in Structure tab.")
            return False

        if not project.aerodynamic_model._mesh_generated:
            messagebox.showerror("Error", "Aerodynamic mesh not generated. Generate mesh in Aerodynamics tab.")
            return False

        return True

    def _analysis_thread(self):
        """Run analysis in background thread."""
        try:
            project = self.project_manager.current_project

            # Prepare analysis configuration
            config = {
                'method': self.method_var.get(),
                'analysis_method': self.method_var.get(),  # Add explicit analysis_method
                'velocity_min': float(self.v_min_var.get()),
                'velocity_max': float(self.v_max_var.get()),
                'velocity_points': int(self.points_var.get()),
                'dynamic_pressure': 50000,  # Default
                'nastran_executable': self._get_current_nastran_path()
            }

            # Progress callback
            def progress_callback(message: str, progress: float):
                self.main_window.root.after(0, lambda: self._update_progress(message, progress))

            # Run analysis
            self.analysis_results = executor.run_flutter_analysis(
                project.structural_model,
                project.aerodynamic_model,
                config,
                progress_callback
            )

            # Update UI in main thread
            self.main_window.root.after(0, self._display_results)

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.main_window.root.after(0, lambda: self._show_analysis_error(error_msg))

    def _update_progress(self, message: str, progress: float):
        """Update progress display."""
        self.progress_bar.set(progress)
        self.progress_label.configure(text=message)

    def _display_results(self):
        """Display analysis results."""
        self.analysis_running = False
        self.run_button.configure(state="normal", text="🚀 Run Flutter Analysis")
        self.progress_bar.set(1.0)
        self.export_button.configure(state="normal")

        if not self.analysis_results or not self.analysis_results.get("success", False):
            error = self.analysis_results.get("error", "Unknown error") if self.analysis_results else "No results"
            messagebox.showerror("Analysis Failed", f"Analysis failed:\n{error}")
            return

        # Update summary
        self._update_summary_display()

        # Update detailed results
        self._update_detailed_display()

        # Show success message
        critical_speed = self.analysis_results.get("critical_flutter_speed", "N/A")
        critical_freq = self.analysis_results.get("critical_flutter_frequency", "N/A")
        method = self.analysis_results.get("method", "Unknown")

        messagebox.showinfo("Analysis Complete",
                          f"Flutter analysis completed successfully!\n\n"
                          f"Method: {method}\n"
                          f"Critical Flutter Speed: {critical_speed} m/s\n"
                          f"Critical Flutter Frequency: {critical_freq} Hz")

    def _update_summary_display(self):
        """Update summary results display."""
        # Update critical results
        speed = self.analysis_results.get("critical_flutter_speed")
        freq = self.analysis_results.get("critical_flutter_frequency")
        method = self.analysis_results.get("method", "Unknown")

        if speed is not None:
            self.flutter_speed_label.configure(text=f"Flutter Speed\n{speed:.1f} m/s")
        else:
            self.flutter_speed_label.configure(text="Flutter Speed\nN/A")

        if freq is not None:
            self.flutter_freq_label.configure(text=f"Flutter Frequency\n{freq:.1f} Hz")
        else:
            self.flutter_freq_label.configure(text="Flutter Frequency\nN/A")

        self.method_result_label.configure(text=f"Analysis Method: {method}")

    def _update_detailed_display(self):
        """Update detailed results display."""
        self.detailed_text.delete("1.0", "end")

        # Format detailed results
        detailed_text = json.dumps(self.analysis_results, indent=2, default=str)
        self.detailed_text.insert("1.0", detailed_text)

    def _show_analysis_error(self, error_msg: str):
        """Show analysis error."""
        self.analysis_running = False
        self.run_button.configure(state="normal", text="🚀 Run Flutter Analysis")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Analysis failed")

        messagebox.showerror("Analysis Error", error_msg)

    def _generate_bdf(self):
        """Generate NASTRAN BDF file."""
        if not self._validate_models():
            return

        try:
            project = self.project_manager.current_project

            # Choose output file
            file_path = filedialog.asksaveasfilename(
                title="Save BDF File",
                defaultextension=".bdf",
                filetypes=[("BDF files", "*.bdf"), ("All files", "*.*")],
                initialfile="panel_flutter_analysis.bdf"
            )

            if not file_path:
                return

            # Generate BDF
            result = executor.generate_bdf_file(
                project.structural_model,
                project.aerodynamic_model,
                Path(file_path)
            )

            if result.get("success", False):
                # Display preview
                self.bdf_text.delete("1.0", "end")
                preview = result.get("content_preview", "BDF generated successfully")
                self.bdf_text.insert("1.0", preview)

                messagebox.showinfo("BDF Generated",
                                  f"BDF file generated successfully!\n\n"
                                  f"File: {file_path}\n"
                                  f"Lines: {result.get('bdf_lines', 'Unknown')}")
            else:
                messagebox.showerror("BDF Generation Failed",
                                   f"Failed to generate BDF file:\n{result.get('error', 'Unknown error')}")

        except Exception as e:
            messagebox.showerror("Error", f"BDF generation failed:\n{str(e)}")

    def _export_results(self):
        """Export analysis results."""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No analysis results to export. Run analysis first.")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Analysis Results",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="flutter_analysis_results.json"
            )

            if not file_path:
                return

            with open(file_path, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)

            messagebox.showinfo("Export Complete", f"Analysis results exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")

    def refresh(self):
        """Refresh panel with current data."""
        # Reset displays
        self.flutter_speed_label.configure(text="Flutter Speed\n-- m/s")
        self.flutter_freq_label.configure(text="Flutter Frequency\n-- Hz")
        self.method_result_label.configure(text="Analysis Method: Not Run")
        self.detailed_text.delete("1.0", "end")
        self.bdf_text.delete("1.0", "end")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready to run analysis")

    def on_show(self):
        """Called when panel is shown."""
        self.refresh()

    def run_analysis(self):
        """Run NASTRAN analysis (legacy compatibility)."""
        self._run_analysis()