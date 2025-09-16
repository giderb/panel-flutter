"""NASTRAN executable auto-detection utility."""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional


def find_nastran_executables() -> List[str]:
    """Auto-detect NASTRAN executables on the system."""
    nastran_paths = []
    system = platform.system().lower()

    if system == "windows":
        nastran_paths.extend(_find_windows_nastran())
    elif system == "linux":
        nastran_paths.extend(_find_linux_nastran())
    elif system == "darwin":  # macOS
        nastran_paths.extend(_find_macos_nastran())

    # Check PATH
    nastran_paths.extend(_find_nastran_in_path())

    # Remove duplicates and verify executables
    verified_paths = []
    for path in set(nastran_paths):
        if _verify_nastran_executable(path):
            verified_paths.append(path)

    return sorted(verified_paths)


def _find_windows_nastran() -> List[str]:
    """Find NASTRAN on Windows systems."""
    paths = []

    # Common MSC.Software installation directories
    common_dirs = [
        "C:\\MSC.Software",
        "C:\\Program Files\\MSC.Software",
        "C:\\Program Files (x86)\\MSC.Software",
        "C:\\MSC",
        "C:\\NASTRAN"
    ]

    for base_dir in common_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.lower() in ["nastran.exe", "nastran.bat"]:
                        full_path = os.path.join(root, file)
                        # Check if it's in a bin directory (likely the real executable)
                        if "bin" in root.lower():
                            paths.append(full_path)

    return paths


def _find_linux_nastran() -> List[str]:
    """Find NASTRAN on Linux systems."""
    paths = []

    # Common installation directories
    common_dirs = [
        "/opt/msc",
        "/usr/local/msc",
        "/opt/nastran",
        "/usr/local/nastran",
        "/opt/MSC.Software",
        "/usr/local/MSC.Software"
    ]

    for base_dir in common_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.lower() == "nastran":
                        full_path = os.path.join(root, file)
                        if "bin" in root.lower() and os.access(full_path, os.X_OK):
                            paths.append(full_path)

    return paths


def _find_macos_nastran() -> List[str]:
    """Find NASTRAN on macOS systems."""
    paths = []

    # Common installation directories on macOS
    common_dirs = [
        "/Applications/MSC.Software",
        "/opt/msc",
        "/usr/local/msc",
        "/opt/nastran",
        "/usr/local/nastran"
    ]

    for base_dir in common_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.lower() == "nastran":
                        full_path = os.path.join(root, file)
                        if "bin" in root.lower() and os.access(full_path, os.X_OK):
                            paths.append(full_path)

    return paths


def _find_nastran_in_path() -> List[str]:
    """Find NASTRAN executables in system PATH."""
    paths = []

    try:
        # Try to find nastran in PATH
        if platform.system().lower() == "windows":
            result = subprocess.run(["where", "nastran"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        paths.append(line.strip())
        else:
            result = subprocess.run(["which", "nastran"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                paths.append(result.stdout.strip())
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return paths


def _verify_nastran_executable(path: str) -> bool:
    """Verify that the given path is a valid NASTRAN executable."""
    if not os.path.isfile(path):
        return False

    try:
        # Check if file is executable
        if not os.access(path, os.R_OK):
            return False

        # On Windows, check extension
        if platform.system().lower() == "windows":
            if not path.lower().endswith(('.exe', '.bat')):
                return False

        # Try to get version info (timeout quickly)
        result = subprocess.run([path, "-version"],
                              capture_output=True, text=True, timeout=5)

        # Check if output contains NASTRAN-related keywords
        output = (result.stdout + result.stderr).lower()
        nastran_keywords = ["nastran", "msc", "software", "version"]

        return any(keyword in output for keyword in nastran_keywords)

    except (subprocess.TimeoutExpired, subprocess.SubprocessError,
            FileNotFoundError, PermissionError):
        # If we can't run it, but it looks like NASTRAN, still consider it valid
        filename = os.path.basename(path).lower()
        return "nastran" in filename


def get_default_nastran_path() -> Optional[str]:
    """Get the best default NASTRAN path."""
    paths = find_nastran_executables()

    if not paths:
        return "nastran"  # Fallback to PATH

    # Prefer paths with version numbers (more specific installations)
    versioned_paths = [p for p in paths if any(c.isdigit() for c in p)]
    if versioned_paths:
        return versioned_paths[0]

    return paths[0]


if __name__ == "__main__":
    """Test the NASTRAN detection."""
    print("Searching for NASTRAN executables...")
    paths = find_nastran_executables()

    if paths:
        print(f"Found {len(paths)} NASTRAN executable(s):")
        for i, path in enumerate(paths, 1):
            print(f"  {i}. {path}")
        print(f"\nDefault: {get_default_nastran_path()}")
    else:
        print("No NASTRAN executables found.")