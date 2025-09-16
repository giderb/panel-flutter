#!/usr/bin/env python3
"""Simple run script for the NASTRAN Panel Flutter Analysis GUI."""

import sys
import os
from pathlib import Path

def main():
    """Run the application with proper error handling."""

    print("NASTRAN Panel Flutter Analysis GUI")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or later is required.")
        print(f"Current version: {sys.version}")
        return 1

    # Test imports
    try:
        print("Testing imports...")

        import customtkinter as ctk
        print("✓ customtkinter")

        from gui.theme_manager import ThemeManager
        print("✓ theme_manager")

        from gui.project_manager import ProjectManager
        print("✓ project_manager")

        from models.material import PredefinedMaterials
        print("✓ material models")

        from utils.logger import setup_logger
        from utils.config import Config
        print("✓ utilities")

        print("\nAll imports successful!")

    except ImportError as e:
        print(f"Import error: {e}")
        print("\nPlease install required packages:")
        print("pip install -r requirements.txt")
        return 1

    # Try to run the GUI
    try:
        print("\nStarting GUI...")
        from main import main as run_main
        return run_main()

    except Exception as e:
        print(f"Error starting GUI: {e}")
        print("\nThis may be due to:")
        print("1. Missing display (if running on server)")
        print("2. Missing dependencies")
        print("3. Configuration issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())