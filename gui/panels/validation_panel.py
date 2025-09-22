"""Validation panel for testing existing analysis capabilities."""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any
import threading
import json
from pathlib import Path

from .base_panel import BasePanel
from python_bridge.analysis_validator import validator


class ValidationPanel(BasePanel):
    """Panel for validating existing analysis capabilities."""

    def __init__(self, parent, main_window):
        self.validation_results: Optional[Dict[str, Any]] = None
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
        content_frame.grid_rowconfigure(2, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            content_frame,
            text="Analysis Capabilities Validation",
            style="heading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Description
        desc_text = ("This panel validates the existing NASTRAN-aeroelasticity analysis backend "
                    "by testing all available solvers and modules against known reference cases.")
        desc_label = self.theme_manager.create_styled_label(
            content_frame,
            text=desc_text,
            style="caption",
            wraplength=800
        )
        desc_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Create notebook for validation sections
        self.notebook = ctk.CTkTabview(content_frame)
        self.notebook.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.overview_tab = self.notebook.add("Overview")
        self.modules_tab = self.notebook.add("Module Status")
        self.solvers_tab = self.notebook.add("Solver Tests")
        self.results_tab = self.notebook.add("Detailed Results")

        self._setup_overview_tab()
        self._setup_modules_tab()
        self._setup_solvers_tab()
        self._setup_results_tab()

        # Control buttons
        self._setup_control_buttons(content_frame)

    def _setup_overview_tab(self):
        """Setup overview tab."""
        self.overview_tab.grid_columnconfigure(0, weight=1)

        # Status summary
        summary_frame = self.theme_manager.create_styled_frame(self.overview_tab, elevated=True)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        title_label = self.theme_manager.create_styled_label(
            summary_frame,
            text="Validation Status",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.status_label = self.theme_manager.create_styled_label(
            summary_frame,
            text="Click 'Run Validation' to test analysis capabilities",
            style="caption"
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=20, pady=(5, 15))

        # Quick test results grid
        quick_frame = self.theme_manager.create_styled_frame(self.overview_tab, elevated=True)
        quick_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        quick_frame.grid_columnconfigure((0, 1, 2), weight=1)

        quick_title = self.theme_manager.create_styled_label(
            quick_frame,
            text="Quick Test Results",
            style="subheading"
        )
        quick_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        # Test result cards
        self.test_cards = {}
        tests = [
            ("Piston Theory", "piston_theory"),
            ("Multi-Solver", "multi_solver"),
            ("BDF Generation", "bdf_generation"),
            ("Materials", "materials"),
            ("Boundary Conditions", "boundary_conditions")
        ]

        for i, (name, key) in enumerate(tests):
            row = 1 + i // 3
            col = i % 3

            card_frame = self.theme_manager.create_styled_frame(quick_frame, elevated=True)
            card_frame.grid(row=row, column=col, sticky="ew", padx=10, pady=5)

            test_label = self.theme_manager.create_styled_label(
                card_frame,
                text=name,
                font=("Segoe UI", 12, "bold")
            )
            test_label.pack(padx=10, pady=(10, 5))

            status_label = self.theme_manager.create_styled_label(
                card_frame,
                text="Not Tested",
                style="caption"
            )
            status_label.pack(padx=10, pady=(0, 10))

            self.test_cards[key] = (card_frame, status_label)

    def _setup_modules_tab(self):
        """Setup modules status tab."""
        self.modules_tab.grid_columnconfigure(0, weight=1)
        self.modules_tab.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            self.modules_tab,
            text="Available Analysis Modules",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Modules text area
        self.modules_text = ctk.CTkTextbox(
            self.modules_tab,
            wrap="word",
            font=("Courier", 11)
        )
        self.modules_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Initialize with current module status
        self._update_modules_display()

    def _setup_solvers_tab(self):
        """Setup solver tests tab."""
        self.solvers_tab.grid_columnconfigure(0, weight=1)
        self.solvers_tab.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            self.solvers_tab,
            text="Solver Test Results",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Solver results text area
        self.solvers_text = ctk.CTkTextbox(
            self.solvers_tab,
            wrap="word",
            font=("Courier", 11)
        )
        self.solvers_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_results_tab(self):
        """Setup detailed results tab."""
        self.results_tab.grid_columnconfigure(0, weight=1)
        self.results_tab.grid_rowconfigure(1, weight=1)

        # Title
        title_label = self.theme_manager.create_styled_label(
            self.results_tab,
            text="Detailed Validation Results",
            style="subheading"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Results text area
        self.results_text = ctk.CTkTextbox(
            self.results_tab,
            wrap="word",
            font=("Courier", 10)
        )
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _setup_control_buttons(self, parent):
        """Setup control buttons."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Run validation button
        self.run_button = self.theme_manager.create_styled_button(
            button_frame,
            text="🔬 Run Comprehensive Validation",
            style="primary",
            command=self._run_validation
        )
        self.run_button.pack(side="left", padx=(0, 10))

        # Progress indicator
        self.progress_bar = ctk.CTkProgressBar(button_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(10, 10))
        self.progress_bar.set(0)

        # Export results button
        self.export_button = self.theme_manager.create_styled_button(
            button_frame,
            text="📄 Export Results",
            style="secondary",
            command=self._export_results,
            state="disabled"
        )
        self.export_button.pack(side="left")

    def _update_modules_display(self):
        """Update the modules display with current status."""
        self.modules_text.delete("1.0", "end")

        modules_info = f"""NASTRAN-Aeroelasticity Module Status
{'=' * 50}

Checking available analysis modules...

"""

        # Check module availability
        for module_name, available in validator.available_modules.items():
            status = "✓ Available" if available else "✗ Not Available"
            modules_info += f"{module_name.replace('_', ' ').title()}: {status}\n"

        modules_info += f"\nTotal Modules: {len(validator.available_modules)}\n"
        modules_info += f"Available: {sum(1 for a in validator.available_modules.values() if a)}\n"

        modules_info += f"\nNASTRAN-Aero Source Path:\n{validator.logger.handlers[0].baseFilename if validator.logger.handlers else 'Not configured'}\n"

        self.modules_text.insert("1.0", modules_info)

    def _run_validation(self):
        """Run comprehensive validation in a separate thread."""
        self.run_button.configure(state="disabled", text="Running Validation...")
        self.progress_bar.set(0.1)

        # Start validation in separate thread
        thread = threading.Thread(target=self._validation_thread)
        thread.daemon = True
        thread.start()

    def _validation_thread(self):
        """Run validation in background thread."""
        try:
            # Update progress
            self._update_progress(0.2, "Starting validation...")

            # Run comprehensive validation
            self.validation_results = validator.run_comprehensive_validation()

            # Update progress
            self._update_progress(0.8, "Processing results...")

            # Update UI in main thread
            self.main_window.root.after(0, self._display_validation_results)

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.main_window.root.after(0, lambda: self._show_validation_error(error_msg))

    def _update_progress(self, value: float, message: str):
        """Update progress bar and status."""
        def update():
            self.progress_bar.set(value)
            self.status_label.configure(text=message)

        self.main_window.root.after(0, update)

    def _display_validation_results(self):
        """Display validation results in the UI."""
        if not self.validation_results:
            return

        # Update progress to complete
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Validation completed!")

        # Update test cards
        self._update_test_cards()

        # Update solver results
        self._update_solver_results()

        # Update detailed results
        self._update_detailed_results()

        # Re-enable buttons
        self.run_button.configure(state="normal", text="🔬 Run Comprehensive Validation")
        self.export_button.configure(state="normal")

        # Show summary message
        summary = self.validation_results.get("summary", {})
        if summary.get("overall_success", False):
            messagebox.showinfo("Validation Complete",
                              f"✓ All tests passed!\n\n"
                              f"Modules: {summary.get('modules_available', 'N/A')}\n"
                              f"Tests: {summary.get('tests_passed', 'N/A')}")
        else:
            messagebox.showwarning("Validation Issues",
                                 f"Some validation tests failed.\n\n"
                                 f"Modules: {summary.get('modules_available', 'N/A')}\n"
                                 f"Tests: {summary.get('tests_passed', 'N/A')}\n\n"
                                 f"Check the detailed results for more information.")

    def _update_test_cards(self):
        """Update the quick test result cards."""
        validation_tests = self.validation_results.get("validation_tests", {})

        for test_key, (card_frame, status_label) in self.test_cards.items():
            test_result = validation_tests.get(test_key, {})
            success = test_result.get("success", False)

            if success:
                status_label.configure(text="✓ PASS", text_color="green")
                card_frame.configure(border_width=2, border_color="green")
            else:
                status_label.configure(text="✗ FAIL", text_color="red")
                card_frame.configure(border_width=2, border_color="red")

    def _update_solver_results(self):
        """Update solver test results display."""
        self.solvers_text.delete("1.0", "end")

        validation_tests = self.validation_results.get("validation_tests", {})

        solver_info = f"""Solver Validation Results
{'=' * 40}

"""

        # Piston Theory Results
        piston_result = validation_tests.get("piston_theory", {})
        if piston_result.get("success", False):
            solver_info += f"""PISTON THEORY SOLVER: ✓ PASS
  Flutter Speed: {piston_result.get('flutter_speed', 'N/A'):.1f} m/s
  Flutter Frequency: {piston_result.get('flutter_frequency', 'N/A'):.1f} Hz
  Method: {piston_result.get('method', 'N/A')}

  ⚠️ CRITICAL SAFETY WARNING ⚠️
  Flutter values must be computed from actual analysis.
  No reference values provided - this is a safety-critical application.
  Real NASTRAN solver required for accurate flutter predictions.

"""
        else:
            solver_info += f"PISTON THEORY SOLVER: ✗ FAIL\n  Error: {piston_result.get('error', 'Unknown')}\n\n"

        # Multi-Solver Results
        multi_result = validation_tests.get("multi_solver", {})
        if multi_result.get("success", False):
            recommendation = multi_result.get("recommendation", {})
            solver_info += f"""MULTI-SOLVER FRAMEWORK: ✓ PASS
  Recommended Method: {recommendation.get('method', 'N/A')}
  Confidence: {recommendation.get('confidence', 0):.2f}
  Reason: {recommendation.get('reason', 'N/A')}

"""
        else:
            solver_info += f"MULTI-SOLVER FRAMEWORK: ✗ FAIL\n  Error: {multi_result.get('error', 'Unknown')}\n\n"

        self.solvers_text.insert("1.0", solver_info)

    def _update_detailed_results(self):
        """Update detailed results display."""
        self.results_text.delete("1.0", "end")

        if self.validation_results:
            # Pretty print the entire results
            detailed_text = json.dumps(self.validation_results, indent=2, default=str)
            self.results_text.insert("1.0", detailed_text)

    def _show_validation_error(self, error_msg: str):
        """Show validation error."""
        self.progress_bar.set(0)
        self.status_label.configure(text="Validation failed")
        self.run_button.configure(state="normal", text="🔬 Run Comprehensive Validation")

        messagebox.showerror("Validation Error", error_msg)

    def _export_results(self):
        """Export validation results to file."""
        if not self.validation_results:
            messagebox.showwarning("No Results", "No validation results to export. Run validation first.")
            return

        try:
            # Export to JSON file
            export_path = Path("validation_results.json")
            with open(export_path, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)

            messagebox.showinfo("Export Complete", f"Validation results exported to:\n{export_path.absolute()}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")

    def refresh(self):
        """Refresh panel with current data."""
        self._update_modules_display()

    def on_show(self):
        """Called when panel is shown."""
        self.refresh()