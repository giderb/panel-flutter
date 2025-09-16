#!/usr/bin/env python3
"""
NASTRAN Panel Flutter Analysis GUI

A modern, sleek GUI application for supersonic panel flutter analysis using NASTRAN
and the nastran-aeroelasticity library.

Built with customtkinter for a modern, professional appearance.
"""

import sys
import os
import threading
import logging
from pathlib import Path

# Add the nastran-aeroelasticity source to Python path
NASTRAN_AERO_PATH = Path(__file__).parent / "nastran-aeroelasticity" / "src"
if NASTRAN_AERO_PATH.exists():
    sys.path.insert(0, str(NASTRAN_AERO_PATH))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Import our custom modules
from gui.main_window import MainWindow
from gui.project_manager import ProjectManager
from gui.theme_manager import ThemeManager
from utils.logger import setup_logger
from utils.config import Config

# Configure matplotlib for better integration
try:
    plt.style.use('seaborn-v0_8')
except Exception:
    # Fallback to default style if seaborn style not available
    pass

def main():
    """Main application entry point."""

    # Setup logging
    logger = setup_logger()
    logger.info("Starting NASTRAN Panel Flutter Analysis GUI")

    try:
        # Test if we have a display available
        import tkinter as tk
        try:
            test_root = tk.Tk()
            test_root.withdraw()  # Hide the test window
            test_root.destroy()
        except tk.TclError as e:
            logger.error(f"No display available: {e}")
            print("Error: No display available. This application requires a GUI environment.")
            print("If running on a server, please use X11 forwarding or a virtual display.")
            return 1

        # Create and configure main window first
        root = ctk.CTk()

        # Initialize customtkinter with error handling
        try:
            ctk.set_appearance_mode("dark")  # Modern dark theme
            ctk.set_default_color_theme("blue")  # Professional blue theme
        except Exception as e:
            logger.warning(f"CustomTkinter theme setting failed: {e}")
            # Continue with defaults
        root.title("NASTRAN Panel Flutter Analysis")
        root.geometry("1400x900")
        root.minsize(1200, 800)

        # Set window icon (if available)
        # Note: Icon file not included - add icon.ico to project root if needed
        # try:
        #     root.iconbitmap("icon.ico")
        # except:
        #     pass

        # Initialize application components
        config = Config()
        theme_manager = ThemeManager()
        project_manager = ProjectManager()

        # Create main application window
        app = MainWindow(root, config, theme_manager, project_manager, logger)

        # Start the application
        logger.info("Application initialized successfully")
        root.mainloop()

    except Exception as e:
        logger.error(f"Fatal error during application startup: {e}")
        messagebox.showerror(
            "Fatal Error",
            f"Failed to start the application:\n{e}\n\nPlease check the logs for details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()