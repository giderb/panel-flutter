"""
Updated Analysis Panel for Validated Flutter System
====================================================
Replaces gui/panels/analysis_panel.py
"""

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
    """Panel for executing validated flutter analysis."""

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
        content_frame.grid_rowconfigure(3, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            content_frame,
            text="Flutter Analysis Execution",
            style="heading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Analysis method selection
        self._setup_method_selection(content_frame)
        
        # NASTRAN settings
        self._setup_nastran_settings(content_frame)

        # Analysis configuration
        self._setup_analysis_config(content_frame)

        # Results display
        self._setup_results_display(content_frame)

        # Control buttons
        self._setup_control_buttons(content_frame)

    def _setup_method_selection(self, parent):
        """Setup analysis method selection."""
        method_frame = self.theme_manager.create_styled_frame(parent)
        method_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        method_label = self.theme_manager.create_styled_label(
            method_frame, text="Analysis Method:", style="subheading"
        )
        method_label.pack(side="left", padx=(0, 10))
        
        self.method_var = tk.StringVar(value="physics")
        
        methods = [
            ("Physics-Based", "physics"),
            ("NASTRAN Only", "nastran"),
            ("Both (Validated)", "both")
        ]
        
        for text, value in methods:
            radio = ctk.CTkRadioButton(
                method_frame,
                text=text,
                variable=self.method_var,
                value=value
            )
            radio.pack(side="left", padx=10)

    def _setup_nastran_settings(self, parent):
        """Setup NASTRAN solver settings section."""
        nastran_frame = self.theme_manager.create_styled_frame(parent)
        nastran_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        nastran_frame.grid_columnconfigure(1, weight=1)

        # NASTRAN executable path
        path_label = self.theme_manager.create_styled_label(
            nastran_frame, text="NASTRAN Path:"
        )
        path_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.nastran_path_var = tk.StringVar()
        self.nastran_path_entry = ctk.CTkEntry(
            nastran_frame,
            textvariable=self.nastran_path_var,
            placeholder_text="Path to NASTRAN executable"
        )
        self.nastran_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Browse button
        browse_btn = ctk.CTkButton(
            nastran_frame,
            text="Browse",
            width=80,
            command=self._browse_nastran
        )
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # Auto-detect button
        detect_btn = ctk.CTkButton(
            nastran_frame,
            text="Auto-Detect",
            width=100,
            command=self._auto_detect_nastran
        )
        detect_btn.grid(row=0, column=3, padx=5, pady=5)

        # Status label
        self.nastran_status_label = self.theme_manager.create_styled_label(
            nastran_frame, text="NASTRAN: Not configured"
        )
        self.nastran_status_label.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=2)

        # Auto-detect on startup
        self._auto_detect_nastran()

    def _setup_analysis_config(self, parent):
        """Setup analysis configuration section."""
        config_frame = self.theme_manager.create_styled_frame(parent)
        config_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)

        # Configuration grid
        params = [
            ("Number of Modes:", "n_modes", "20"),
            ("Mesh Density (NX):", "mesh_nx", "20"),
            ("Mesh Density (NY):", "mesh_ny", "20"),
            ("Min Velocity (m/s):", "velocity_min", "100"),
            ("Max Velocity (m/s):", "velocity_max", "2000"),
            ("Velocity Points:", "velocity_points", "50")
        ]

        self.config_vars = {}
        for i, (label_text, key, default) in enumerate(params):
            row = i // 3
            col = (i % 3) * 2

            label = self.theme_manager.create_styled_label(config_frame, text=label_text)
            label.grid(row=row, column=col, sticky="e", padx=5, pady=5)

            var = tk.StringVar(value=default)
            self.config_vars[key] = var

            entry = ctk.CTkEntry(config_frame, textvariable=var, width=100)
            entry.grid(row=row, column=col+1, sticky="w", padx=5, pady=5)

    def _setup_results_display(self, parent):
        """Setup results display section."""
        results_frame = self.theme_manager.create_styled_frame(parent, elevated=True)
        results_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        # Results header
        header_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        results_label = self.theme_manager.create_styled_label(
            header_frame, text="Analysis Results", style="subheading"
        )
        results_label.pack(side="left")

        # Critical results display
        critical_frame = ctk.CTkFrame(results_frame)
        critical_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Flutter speed
        self.flutter_speed_label = self.theme_manager.create_styled_label(
            critical_frame,
            text="Flutter Speed\n-- m/s",
            style="metric"
        )
        self.flutter_speed_label.pack(side="left", padx=20, pady=10)

        # Flutter frequency
        self.flutter_freq_label = self.theme_manager.create_styled_label(
            critical_frame,
            text="Flutter Frequency\n-- Hz",
            style="metric"
        )
        self.flutter_freq_label.pack(side="left", padx=20, pady=10)

        # Validation status
        self.validation_label = self.theme_manager.create_styled_label(
            critical_frame,
            text="Validation\nPending",
            style="metric"
        )
        self.validation_label.pack(side="left", padx=20, pady=10)

        # Detailed results text
        self.results_text = ctk.CTkTextbox(
            results_frame,
            height=200
        )
        self.results_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(results_frame)
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.progress_bar.set(0)

        self.progress_label = self.theme_manager.create_styled_label(
            results_frame, text="Ready to run analysis"
        )
        self.progress_label.grid(row=4, column=0, sticky="w", padx=10, pady=2)

    def _setup_control_buttons(self, parent):
        """Setup control buttons."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=10)

        # Run Analysis button
        self.run_button = ctk.CTkButton(
            button_frame,
            text="🚀 Run Flutter Analysis",
            command=self._run_analysis,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.run_button.pack(side="left", padx=5)

        # Generate BDF button
        self.bdf_button = ctk.CTkButton(
            button_frame,
            text="📄 Generate BDF Only",
            command=self._generate_bdf,
            height=40
        )
        self.bdf_button.pack(side="left", padx=5)

        # Validate button
        validate_btn = ctk.CTkButton(
            button_frame,
            text="✓ Validate Setup",
            command=self._validate_setup,
            height=40
        )
        validate_btn.pack(side="left", padx=5)

        # Export button
        export_btn = ctk.CTkButton(
            button_frame,
            text="💾 Export Results",
            command=self._export_results,
            height=40
        )
        export_btn.pack(side="left", padx=5)

    def _browse_nastran(self):
        """Browse for NASTRAN executable."""
        filename = filedialog.askopenfilename(
            title="Select NASTRAN Executable",
            filetypes=[("Executable files", "*.exe *.bat"), ("All files", "*.*")]
        )
        if filename:
            self.nastran_path_var.set(filename)
            self._validate_nastran_path()

    def _auto_detect_nastran(self):
        """Auto-detect NASTRAN installation."""
        self.nastran_status_label.configure(text="Searching for NASTRAN...")
        
        paths = find_nastran_executables()
        if paths:
            self.nastran_path_var.set(paths[0])
            self.nastran_status_label.configure(
                text=f"NASTRAN found: {Path(paths[0]).name}"
            )
        else:
            self.nastran_status_label.configure(
                text="NASTRAN not found - physics-based analysis available"
            )

    def _validate_nastran_path(self):
        """Validate NASTRAN executable path."""
        path = self.nastran_path_var.get()
        if path and Path(path).exists():
            self.nastran_status_label.configure(text=f"NASTRAN: {Path(path).name}")
            return True
        else:
            self.nastran_status_label.configure(text="NASTRAN: Invalid path")
            return False

    def _validate_setup(self):
        """Validate the analysis setup."""
        # Get current project models
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("Error", "No project loaded")
            return

        validation = executor.validate_analysis(
            project.geometry,
            project.aerodynamic_config
        )

        if validation['valid']:
            message = "✅ Analysis setup is valid\n"
            if validation['warnings']:
                message += "\n⚠️ Warnings:\n" + "\n".join(validation['warnings'])
            messagebox.showinfo("Validation", message)
        else:
            message = "❌ Analysis setup has errors:\n\n"
            message += "\n".join(validation['errors'])
            if validation['warnings']:
                message += "\n\n⚠️ Warnings:\n" + "\n".join(validation['warnings'])
            messagebox.showerror("Validation Error", message)

    def _run_analysis(self):
        """Run flutter analysis."""
        if self.analysis_running:
            return

        # Validate project
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("Error", "No project loaded")
            return

        if not project.geometry or not project.aerodynamic_config:
            messagebox.showerror("Error", "Please define geometry and aerodynamic configuration first")
            return

        # Prepare configuration
        config = {
            'n_modes': int(self.config_vars['n_modes'].get()),
            'mesh_nx': int(self.config_vars['mesh_nx'].get()),
            'mesh_ny': int(self.config_vars['mesh_ny'].get()),
            'velocity_min': float(self.config_vars['velocity_min'].get()),
            'velocity_max': float(self.config_vars['velocity_max'].get()),
            'velocity_points': int(self.config_vars['velocity_points'].get()),
            'working_dir': Path.cwd() / 'analysis_output'
        }

        # Set method
        method = self.method_var.get()
        if method == "nastran":
            config['use_nastran'] = True
            config['execute_nastran'] = True
            if not self._validate_nastran_path():
                messagebox.showerror("Error", "Valid NASTRAN path required for NASTRAN analysis")
                return
        elif method == "both":
            config['use_nastran'] = True
            config['execute_nastran'] = self._validate_nastran_path()

        # Create output directory
        config['working_dir'].mkdir(exist_ok=True)

        # Start analysis in thread
        self.analysis_running = True
        self.run_button.configure(state="disabled", text="⏳ Running...")
        self.progress_bar.set(0)

        thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(project.geometry, project.aerodynamic_config, config)
        )
        thread.daemon = True
        thread.start()

    def _run_analysis_thread(self, geometry, aerodynamic_config, config):
        """Run analysis in separate thread."""
        try:
            # Progress callback
            def progress_callback(message: str, progress: float):
                self.progress_label.configure(text=message)
                self.progress_bar.set(progress)

            # Run analysis
            self.analysis_results = executor.run_analysis(
                geometry,
                aerodynamic_config,
                config,
                progress_callback
            )

            # Update GUI in main thread
            self.frame.after(0, self._handle_analysis_complete)

        except Exception as e:
            self.frame.after(0, lambda: self._show_analysis_error(str(e)))

    def _handle_analysis_complete(self):
        """Handle analysis completion."""
        self.analysis_running = False
        self.run_button.configure(state="normal", text="🚀 Run Flutter Analysis")

        if self.analysis_results and self.analysis_results.get('success'):
            # Update displays
            self._update_results_display()

            # Show completion message
            critical_speed = self.analysis_results.get('critical_flutter_speed', 0)
            critical_freq = self.analysis_results.get('critical_flutter_frequency', 0)
            validation = self.analysis_results.get('validation_status', 'Unknown')

            if critical_speed > 9000:
                message = "✅ Analysis Complete!\n\nPanel is STABLE (no flutter detected)"
            else:
                message = f"✅ Analysis Complete!\n\n"
                message += f"Critical Flutter Speed: {critical_speed:.1f} m/s\n"
                message += f"Critical Flutter Frequency: {critical_freq:.1f} Hz\n"
                message += f"Validation: {validation}"

            messagebox.showinfo("Analysis Complete", message)

            # Send to results panel
            if "results" in self.main_window.panels:
                self.main_window.panels["results"].load_results(self.analysis_results)

            # Auto-switch to results panel
            self.main_window._show_panel("results")
        else:
            error = self.analysis_results.get('error', 'Unknown error') if self.analysis_results else 'Unknown error'
            self._show_analysis_error(error)

    def _update_results_display(self):
        """Update results display."""
        if not self.analysis_results:
            return

        # Update critical values
        speed = self.analysis_results.get('critical_flutter_speed', 0)
        freq = self.analysis_results.get('critical_flutter_frequency', 0)
        validation = self.analysis_results.get('validation_status', 'Not validated')

        if speed > 9000:
            self.flutter_speed_label.configure(text="Flutter Speed\nNo Flutter")
        else:
            self.flutter_speed_label.configure(text=f"Flutter Speed\n{speed:.1f} m/s")

        self.flutter_freq_label.configure(text=f"Flutter Frequency\n{freq:.1f} Hz")

        # Update validation status with color
        if "EXCELLENT" in validation or "VALIDATED" in validation:
            color = "green"
        elif "GOOD" in validation or "ACCEPTABLE" in validation:
            color = "orange"
        else:
            color = "red"

        self.validation_label.configure(
            text=f"Validation\n{validation.split(':')[0]}"
        )

        # Update detailed text
        self.results_text.delete("1.0", "end")
        
        detailed = f"""═══════════════════════════════════════════
FLUTTER ANALYSIS RESULTS
═══════════════════════════════════════════

Method: {self.analysis_results.get('method', 'Unknown')}
Analysis Type: {self.analysis_results.get('analysis_type', 'Unknown')}
Converged: {self.analysis_results.get('converged', False)}

CRITICAL RESULTS:
• Flutter Speed: {speed:.1f} m/s
• Flutter Frequency: {freq:.1f} Hz
• Flutter Mode: {self.analysis_results.get('critical_flutter_mode', 0)}
• Dynamic Pressure: {self.analysis_results.get('critical_dynamic_pressure', 0):.0f} Pa

CONFIGURATION:
{self.analysis_results.get('configuration', {}).get('panel_dimensions', 'Unknown')}
{self.analysis_results.get('configuration', {}).get('material', 'Unknown')}
Boundary: {self.analysis_results.get('configuration', {}).get('boundary_conditions', 'Unknown')}
Mach: {self.analysis_results.get('configuration', {}).get('mach_number', 0):.2f}

VALIDATION:
{validation}

Safety Margin: {self.analysis_results.get('safety_margin', 0):.1f}%
Stable in Range: {self.analysis_results.get('stable_in_range', False)}

Execution Time: {self.analysis_results.get('execution_time', 0):.2f} seconds
"""
        
        self.results_text.insert("1.0", detailed)
        self.progress_label.configure(text="Analysis complete")
        self.progress_bar.set(1.0)

    def _show_analysis_error(self, error_msg: str):
        """Show analysis error."""
        self.analysis_running = False
        self.run_button.configure(state="normal", text="🚀 Run Flutter Analysis")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Analysis failed")
        messagebox.showerror("Analysis Error", error_msg)

    def _generate_bdf(self):
        """Generate NASTRAN BDF file only."""
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("Error", "No project loaded")
            return

        config = {
            'mesh_nx': int(self.config_vars['mesh_nx'].get()),
            'mesh_ny': int(self.config_vars['mesh_ny'].get()),
            'n_modes': int(self.config_vars['n_modes'].get()),
            'velocity_min': float(self.config_vars['velocity_min'].get()),
            'velocity_max': float(self.config_vars['velocity_max'].get()),
            'working_dir': Path.cwd() / 'analysis_output'
        }

        config['working_dir'].mkdir(exist_ok=True)

        result = executor.generate_bdf_only(
            project.geometry,
            project.aerodynamic_config,
            config
        )

        if result['success']:
            messagebox.showinfo(
                "BDF Generated",
                f"BDF file generated successfully:\n{result['bdf_file']}\n\n"
                f"Lines: {result['bdf_lines']}"
            )
        else:
            messagebox.showerror("Error", result['error'])

    def _export_results(self):
        """Export analysis results."""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No analysis results to export")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt")
            ]
        )

        if filepath:
            try:
                if filepath.endswith('.json'):
                    with open(filepath, 'w') as f:
                        json.dump(self.analysis_results, f, indent=2, default=str)
                elif filepath.endswith('.csv'):
                    # Export key results as CSV
                    import csv
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Parameter', 'Value'])
                        writer.writerow(['Flutter Speed (m/s)', self.analysis_results.get('critical_flutter_speed')])
                        writer.writerow(['Flutter Frequency (Hz)', self.analysis_results.get('critical_flutter_frequency')])
                        writer.writerow(['Flutter Mode', self.analysis_results.get('critical_flutter_mode')])
                        writer.writerow(['Validation', self.analysis_results.get('validation_status')])
                else:
                    # Export as text
                    with open(filepath, 'w') as f:
                        f.write(self.results_text.get("1.0", "end"))

                messagebox.showinfo("Export Complete", f"Results exported to:\n{filepath}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def refresh(self):
        """Refresh panel."""
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready to run analysis")
        if self.analysis_results:
            self._update_results_display()

    def on_show(self):
        """Called when panel is shown."""
        self.refresh()
