"""NASTRAN execution and process management."""

import subprocess
import os
import shutil
import tempfile
import time
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging


class NastranRunner:
    """Handles NASTRAN subprocess execution."""

    def __init__(self, nastran_executable: str = "nastran"):
        self.nastran_exe = nastran_executable
        self.logger = logging.getLogger(__name__)

    def validate_nastran_executable(self) -> bool:
        """Validate that NASTRAN executable is available."""
        # First check if the executable exists
        if not os.path.exists(self.nastran_exe):
            self.logger.error(f"NASTRAN executable not found at: {self.nastran_exe}")
            return False

        # For MSC Nastran, the executable might not support -version flag
        # Just check if file exists and is executable
        if os.path.isfile(self.nastran_exe):
            self.logger.info(f"NASTRAN executable found: {self.nastran_exe}")
            # Check if it's actually an executable (Windows .exe)
            if self.nastran_exe.lower().endswith('.exe'):
                return True

        self.logger.warning(f"NASTRAN executable validation uncertain: {self.nastran_exe}")
        return True  # Allow execution anyway as some NASTRAN versions don't support version check

    def run_analysis(self,
                    bdf_file_path: str,
                    working_dir: Optional[str] = None,
                    timeout: int = 3600,
                    progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Execute NASTRAN analysis.

        Args:
            bdf_file_path: Path to BDF input file
            working_dir: Working directory for execution (defaults to BDF file directory)
            timeout: Execution timeout in seconds
            progress_callback: Progress update callback

        Returns:
            Dictionary with execution results
        """
        bdf_path = Path(bdf_file_path)

        if not bdf_path.exists():
            raise FileNotFoundError(f"BDF file not found: {bdf_file_path}")

        if working_dir is None:
            working_dir = bdf_path.parent
        else:
            working_dir = Path(working_dir)

        working_dir.mkdir(parents=True, exist_ok=True)

        # Get base filename without extension
        job_name = bdf_path.stem

        # Copy BDF to working directory if needed
        if bdf_path.parent != working_dir:
            working_bdf = working_dir / bdf_path.name
            shutil.copy2(bdf_path, working_bdf)
            bdf_file_path = str(working_bdf)

        if progress_callback:
            progress_callback("Starting NASTRAN execution...", 0.1)

        # Prepare NASTRAN command for MSC Nastran
        # MSC Nastran typically uses format: nastran.exe input.bdf
        # Use just the filename when running in the working directory
        cmd = [
            self.nastran_exe,
            bdf_path.name  # Use just the filename, not full path
        ]

        self.logger.info(f"Executing NASTRAN: {' '.join(cmd)}")
        self.logger.info(f"Working directory: {working_dir}")

        try:
            # Start NASTRAN process
            start_time = time.time()

            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor progress
            stdout_lines = []
            stderr_lines = []

            def read_stdout():
                for line in iter(process.stdout.readline, ''):
                    stdout_lines.append(line.strip())
                    self._parse_nastran_progress(line, progress_callback)

            def read_stderr():
                for line in iter(process.stderr.readline, ''):
                    stderr_lines.append(line.strip())

            # Start reader threads
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Wait for completion with timeout
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                raise RuntimeError(f"NASTRAN execution timed out after {timeout} seconds")

            # Wait for reader threads to finish
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            execution_time = time.time() - start_time

            # Check return code
            if process.returncode != 0:
                error_msg = f"NASTRAN execution failed with return code {process.returncode}"
                if stderr_lines:
                    error_msg += f"\nSTDERR:\n" + "\n".join(stderr_lines[-10:])  # Last 10 lines
                raise RuntimeError(error_msg)

            if progress_callback:
                progress_callback("NASTRAN execution completed", 1.0)

            # Check for output files
            f06_file = working_dir / f"{job_name}.f06"
            log_file = working_dir / f"{job_name}.log"

            result = {
                "success": True,
                "return_code": process.returncode,
                "execution_time": execution_time,
                "working_directory": str(working_dir),
                "job_name": job_name,
                "f06_file": str(f06_file) if f06_file.exists() else None,
                "log_file": str(log_file) if log_file.exists() else None,
                "stdout_lines": len(stdout_lines),
                "stderr_lines": len(stderr_lines)
            }

            self.logger.info(f"NASTRAN execution completed successfully in {execution_time:.1f} seconds")
            self.logger.info(f"F06 file: {'Found' if f06_file.exists() else 'Not found'}")

            return result

        except Exception as e:
            self.logger.error(f"NASTRAN execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "working_directory": str(working_dir),
                "job_name": job_name
            }

    def _parse_nastran_progress(self, line: str, progress_callback: Optional[Callable[[str, float], None]]):
        """Parse NASTRAN output for progress information."""
        if not progress_callback:
            return

        line_lower = line.lower().strip()

        # Common NASTRAN progress indicators
        progress_indicators = {
            "executive control deck": (0.1, "Reading executive control"),
            "case control deck": (0.2, "Reading case control"),
            "bulk data deck": (0.3, "Reading bulk data"),
            "normal modes analysis": (0.4, "Computing normal modes"),
            "flutter analysis": (0.6, "Performing flutter analysis"),
            "aerodynamic": (0.5, "Setting up aerodynamics"),
            "eigenvalue": (0.4, "Computing eigenvalues"),
            "solution completed": (0.9, "Solution completed"),
            "end of job": (1.0, "Analysis finished")
        }

        for keyword, (progress, message) in progress_indicators.items():
            if keyword in line_lower:
                progress_callback(message, progress)
                break


def test_nastran_runner():
    """Test the NASTRAN runner."""
    # Test with a simple executable check
    runner = NastranRunner()

    print("Testing NASTRAN executable validation...")
    is_valid = runner.validate_nastran_executable()
    print(f"NASTRAN executable valid: {is_valid}")

    return is_valid


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    test_nastran_runner()