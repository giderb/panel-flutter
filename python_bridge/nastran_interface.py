"""
NASTRAN Interface Module
=========================
Provides interface to NASTRAN solver for flutter analysis.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class F06Parser:
    """
    Parser for NASTRAN .f06 output files.
    Extracts flutter analysis results from SOL 145 output.
    """

    def __init__(self, f06_path: str):
        """
        Initialize F06 parser.

        Args:
            f06_path: Path to .f06 file
        """
        self.f06_path = Path(f06_path)
        self.flutter_data = {}
        self.parsed = False

        if not self.f06_path.exists():
            raise FileNotFoundError(f"F06 file not found: {f06_path}")

    def parse(self) -> Dict:
        """
        Parse the F06 file and extract flutter results.

        Returns:
            Dictionary containing flutter analysis results
        """
        logger.info(f"Parsing F06 file: {self.f06_path}")

        try:
            with open(self.f06_path, 'r') as f:
                content = f.read()

            # Extract flutter summary
            flutter_summary = self._extract_flutter_summary(content)

            # Extract velocity-damping data
            vg_data = self._extract_vg_data(content)

            # Extract velocity-frequency data
            vf_data = self._extract_vf_data(content)

            self.flutter_data = {
                'summary': flutter_summary,
                'vg_data': vg_data,
                'vf_data': vf_data,
                'parsed': True
            }

            self.parsed = True
            logger.info("F06 parsing complete")

            return self.flutter_data

        except Exception as e:
            logger.error(f"Error parsing F06 file: {e}")
            raise

    def _extract_flutter_summary(self, content: str) -> Dict:
        """Extract flutter summary from F06 content"""
        summary = {
            'flutter_speed': None,
            'flutter_frequency': None,
            'flutter_mode': None,
            'damping': None,
            'converged': False
        }

        # Look for flutter summary table
        # Pattern: FLUTTER SUMMARY
        #          VELOCITY  DAMPING  FREQUENCY  MODE
        flutter_pattern = r'FLUTTER\s+SUMMARY.*?VELOCITY.*?DAMPING.*?FREQUENCY.*?MODE\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+(\d+)'

        match = re.search(flutter_pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            summary['flutter_speed'] = float(match.group(1))
            summary['damping'] = float(match.group(2))
            summary['flutter_frequency'] = float(match.group(3))
            summary['flutter_mode'] = int(match.group(4))
            summary['converged'] = True

            logger.info(f"Flutter found: V={summary['flutter_speed']:.1f}, f={summary['flutter_frequency']:.1f} Hz")
        else:
            logger.warning("No flutter summary found in F06 file")

        return summary

    def _extract_vg_data(self, content: str) -> Dict:
        """Extract velocity-damping data"""
        vg_data = {
            'velocities': [],
            'damping': [],
            'modes': []
        }

        # Look for V-g table
        # This is a simplified parser - real implementation would be more robust
        vg_pattern = r'V-G\s+DATA.*?VELOCITY.*?DAMPING.*?MODE([\s\S]*?)(?:\n\s*\n|$)'

        match = re.search(vg_pattern, content, re.IGNORECASE)
        if match:
            data_block = match.group(1)
            # Parse each line
            for line in data_block.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        velocity = float(parts[0])
                        damping = float(parts[1])
                        mode = int(parts[2])

                        vg_data['velocities'].append(velocity)
                        vg_data['damping'].append(damping)
                        vg_data['modes'].append(mode)
                    except (ValueError, IndexError):
                        continue

        return vg_data

    def _extract_vf_data(self, content: str) -> Dict:
        """Extract velocity-frequency data"""
        vf_data = {
            'velocities': [],
            'frequencies': [],
            'modes': []
        }

        # Look for V-f table
        vf_pattern = r'V-F\s+DATA.*?VELOCITY.*?FREQUENCY.*?MODE([\s\S]*?)(?:\n\s*\n|$)'

        match = re.search(vf_pattern, content, re.IGNORECASE)
        if match:
            data_block = match.group(1)
            # Parse each line
            for line in data_block.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        velocity = float(parts[0])
                        frequency = float(parts[1])
                        mode = int(parts[2])

                        vf_data['velocities'].append(velocity)
                        vf_data['frequencies'].append(frequency)
                        vf_data['modes'].append(mode)
                    except (ValueError, IndexError):
                        continue

        return vf_data

    def get_flutter_speed(self) -> Optional[float]:
        """Get critical flutter speed"""
        if not self.parsed:
            self.parse()
        return self.flutter_data.get('summary', {}).get('flutter_speed')

    def get_flutter_frequency(self) -> Optional[float]:
        """Get flutter frequency"""
        if not self.parsed:
            self.parse()
        return self.flutter_data.get('summary', {}).get('flutter_frequency')

    def get_flutter_mode(self) -> Optional[int]:
        """Get flutter mode number"""
        if not self.parsed:
            self.parse()
        return self.flutter_data.get('summary', {}).get('flutter_mode')

    def is_converged(self) -> bool:
        """Check if flutter analysis converged"""
        if not self.parsed:
            self.parse()
        return self.flutter_data.get('summary', {}).get('converged', False)


class NastranRunner:
    """
    Interface to run NASTRAN solver.
    """

    def __init__(self, nastran_executable: str):
        """
        Initialize NASTRAN runner.

        Args:
            nastran_executable: Path to NASTRAN executable
        """
        self.nastran_exe = Path(nastran_executable)
        self.logger = logging.getLogger(__name__)

        if not self.nastran_exe.exists():
            raise FileNotFoundError(f"NASTRAN executable not found: {nastran_executable}")

    def run_analysis(self, bdf_path: str, output_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run NASTRAN analysis.

        Args:
            bdf_path: Path to BDF input file
            output_dir: Optional output directory (default: same as BDF)

        Returns:
            Tuple of (success, message)
        """
        import subprocess

        bdf_file = Path(bdf_path)
        if not bdf_file.exists():
            return False, f"BDF file not found: {bdf_path}"

        if output_dir is None:
            output_dir = bdf_file.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Build NASTRAN command
        cmd = [
            str(self.nastran_exe),
            str(bdf_file),
            f"out={output_dir}",
            "batch=no",
            "old=no"
        ]

        self.logger.info(f"Running NASTRAN: {' '.join(cmd)}")

        try:
            # Run NASTRAN
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                self.logger.info("NASTRAN analysis completed successfully")
                return True, "Analysis completed successfully"
            else:
                error_msg = f"NASTRAN failed with return code {result.returncode}"
                self.logger.error(error_msg)
                self.logger.error(f"STDERR: {result.stderr}")
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "NASTRAN analysis timed out (>1 hour)"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error running NASTRAN: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg


# Module-level convenience functions
def parse_f06(f06_path: str) -> Dict:
    """
    Parse an F06 file and return flutter results.

    Args:
        f06_path: Path to F06 file

    Returns:
        Dictionary of flutter results
    """
    parser = F06Parser(f06_path)
    return parser.parse()


def run_nastran(nastran_exe: str, bdf_path: str, output_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Run NASTRAN analysis.

    Args:
        nastran_exe: Path to NASTRAN executable
        bdf_path: Path to BDF input file
        output_dir: Optional output directory

    Returns:
        Tuple of (success, message)
    """
    runner = NastranRunner(nastran_exe)
    return runner.run_analysis(bdf_path, output_dir)
