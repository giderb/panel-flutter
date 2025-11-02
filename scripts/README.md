# Scripts

This folder contains build scripts and utilities for the Panel Flutter Analysis application.

## Build Scripts

### Executable Builder

- **`build_executable.py`** - Creates standalone executable using PyInstaller

  **Usage:**
  ```bash
  .\.venv\Scripts\python.exe scripts\build_executable.py
  ```

  **Output:**
  - Creates `dist/PanelFlutter.exe` (Windows)
  - Includes all dependencies
  - Single-file executable for easy distribution

  **Requirements:**
  - PyInstaller must be installed: `pip install pyinstaller`
  - All project dependencies must be in requirements.txt

## Future Scripts

Planned utility scripts:
- Data migration tools
- Batch analysis runners
- Result exporters
- Configuration validators

## Adding New Scripts

When adding new scripts:
1. Use descriptive filenames
2. Add shebang line for cross-platform compatibility
3. Include usage documentation in this README
4. Add error handling and logging
5. Make scripts executable: `chmod +x script_name.py`

---

*Last Updated: 2025-11-02*
