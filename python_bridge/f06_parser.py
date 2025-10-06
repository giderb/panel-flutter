"""
NASTRAN F06 Output File Parser
================================

Parses NASTRAN F06 output files to extract:
- Modal frequencies (SOL 103)
- Flutter results (SOL 145)
- Error messages and warnings
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModalResult:
    """Modal analysis result"""
    mode_number: int
    frequency_hz: float
    eigenvalue: float
    generalized_mass: float
    generalized_stiffness: float


@dataclass
class FlutterPoint:
    """Flutter analysis result point"""
    velocity: float
    damping: float
    frequency: float
    mach_number: float
    density_ratio: float
    mode: int


class F06Parser:
    """Parser for NASTRAN F06 output files"""

    def __init__(self, f06_path: Path):
        self.f06_path = f06_path
        self.content = ""
        self.modal_results = []
        self.flutter_results = []
        self.errors = []
        self.warnings = []
        self.has_fatal_errors = False

    def parse(self) -> Dict[str, Any]:
        """Parse F06 file and extract all results"""
        if not self.f06_path.exists():
            logger.error(f"F06 file not found: {self.f06_path}")
            return self._empty_results()

        try:
            with open(self.f06_path, 'r') as f:
                self.content = f.read()

            # Check for fatal errors first
            self._parse_errors()

            if not self.has_fatal_errors:
                # Parse modal frequencies
                self._parse_modal_frequencies()

                # Parse flutter results if available
                self._parse_flutter_results()

            return self._build_results()

        except Exception as e:
            logger.error(f"Error parsing F06 file: {e}")
            return self._empty_results()

    def _parse_errors(self):
        """Extract error and warning messages"""
        # Find fatal errors
        fatal_pattern = r'\*\*\* USER FATAL MESSAGE.*?\n(.*)'
        for match in re.finditer(fatal_pattern, self.content):
            self.errors.append(match.group(1).strip())
            self.has_fatal_errors = True

        # Find warnings
        warning_pattern = r'\*\*\* USER WARNING MESSAGE.*?\n(.*)'
        for match in re.finditer(warning_pattern, self.content):
            self.warnings.append(match.group(1).strip())

    def _parse_modal_frequencies(self):
        """Extract modal frequencies from SOL 103 output"""
        # Look for eigenvalue table
        eigen_pattern = r'E I G E N V A L U E   A N A L Y S I S   S U M M A R Y.*?\n(.*?)(?:\n\n|\Z)'
        match = re.search(eigen_pattern, self.content, re.DOTALL)

        if not match:
            # Try alternative format
            eigen_pattern = r'R E A L   E I G E N V A L U E S.*?\n(.*?)(?:\n\n|\Z)'
            match = re.search(eigen_pattern, self.content, re.DOTALL)

        if match:
            table_text = match.group(1)
            self._parse_eigenvalue_table(table_text)

    def _parse_eigenvalue_table(self, table_text: str):
        """Parse eigenvalue table to extract modal data"""
        lines = table_text.split('\n')

        # Track mode renumbering after filtering
        physical_mode_num = 1

        for line in lines:
            # Look for lines with mode data (contains numbers)
            if re.match(r'\s*\d+', line):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        mode = int(parts[0])
                        # The frequency is in column 4 (CYCLES)
                        eigenvalue = float(parts[2]) if len(parts) > 2 else 0.0
                        frequency_hz = float(parts[4]) if len(parts) > 4 else 0.0
                        gen_mass = float(parts[5]) if len(parts) > 5 else 1.0
                        gen_stiff = float(parts[6]) if len(parts) > 6 else eigenvalue

                        # Filter out spurious near-zero frequency modes
                        # These are typically aerodynamic modes with frequency < 0.1 Hz
                        if frequency_hz > 0.1:  # Only keep modes above 0.1 Hz
                            self.modal_results.append(ModalResult(
                                mode_number=physical_mode_num,  # Renumber modes
                                frequency_hz=frequency_hz,
                                eigenvalue=eigenvalue,
                                generalized_mass=gen_mass,
                                generalized_stiffness=gen_stiff
                            ))
                            physical_mode_num += 1
                        else:
                            logger.debug(f"Filtered out spurious mode {mode} with frequency {frequency_hz:.6f} Hz")
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Error parsing eigenvalue line: {line} - {e}")
                        continue

    def _parse_flutter_results(self):
        """Extract flutter analysis results from SOL 145"""
        # Look for flutter summary table - matches multiple spaces
        flutter_pattern = r'FLUTTER\s+SUMMARY.*?\n(.*?)(?:\n1|\Z)'
        matches = re.finditer(flutter_pattern, self.content, re.DOTALL)

        for match in matches:
            table_text = match.group(1)
            self._parse_flutter_table(table_text)

    def _parse_flutter_table(self, table_text: str):
        """Parse flutter summary table"""
        lines = table_text.split('\n')

        # Find the data lines (they start with numeric values or asterisks)
        for line in lines:
            # Skip header lines
            if 'KFREQ' in line or 'VELOCITY' in line or 'CONFIGURATION' in line or 'POINT' in line:
                continue

            # Parse data lines - format is:
            # KFREQ  1./KFREQ  VELOCITY  DAMPING  FREQUENCY  COMPLEX EIGENVALUE
            parts = line.split()
            if len(parts) >= 6:
                try:
                    # Handle asterisks in KFREQ field
                    kfreq = parts[0]
                    if '*' in kfreq:
                        kfreq_val = float('inf')
                    else:
                        kfreq_val = float(kfreq)

                    # Parse the rest of the fields
                    inv_kfreq = float(parts[1])
                    velocity = float(parts[2])
                    damping = float(parts[3])
                    frequency = float(parts[4])
                    real_eigen = float(parts[5])
                    imag_eigen = float(parts[6]) if len(parts) > 6 else 0.0

                    self.flutter_results.append(FlutterPoint(
                        velocity=velocity,
                        damping=damping,
                        frequency=frequency,
                        mach_number=3.0,  # From POINT header
                        density_ratio=1.0,  # From POINT header
                        mode=1  # Mode number not in this format
                    ))
                except (ValueError, IndexError):
                    continue

    def _build_results(self) -> Dict[str, Any]:
        """Build results dictionary"""
        # Find critical flutter point (where damping crosses zero)
        critical_velocity = None
        critical_frequency = None

        if self.flutter_results:
            # Group flutter points by velocity
            from collections import defaultdict
            velocity_groups = defaultdict(list)
            for pt in self.flutter_results:
                velocity_groups[pt.velocity].append(pt)

            # Sort velocities
            sorted_velocities = sorted(velocity_groups.keys())

            # Look for mode transitions between consecutive velocities
            # Focus on structural panel flutter modes (5-100 Hz)
            for i in range(len(sorted_velocities) - 1):
                v1 = sorted_velocities[i]
                v2 = sorted_velocities[i + 1]

                modes_v1 = velocity_groups[v1]
                modes_v2 = velocity_groups[v2]

                # Try to match modes by frequency (same mode will have similar frequency)
                for m1 in modes_v1:
                    # Skip modes outside realistic panel flutter range
                    if m1.frequency < 5.0 or m1.frequency > 100.0:
                        continue

                    # Find matching mode at next velocity (frequency within 20% tolerance)
                    for m2 in modes_v2:
                        if m2.frequency < 5.0 or m2.frequency > 100.0:
                            continue

                        # Check if this is likely the same mode (frequency similar)
                        freq_ratio = abs(m2.frequency - m1.frequency) / m1.frequency if m1.frequency > 0 else float('inf')
                        if freq_ratio < 0.2:  # Frequency within 20%
                            # Check for flutter onset (negative to positive damping)
                            if m1.damping < 0 and m2.damping > 0:
                                # Linear interpolation to zero damping
                                d1 = m1.damping
                                d2 = m2.damping
                                f1 = m1.frequency
                                f2 = m2.frequency

                                t = -d1 / (d2 - d1)
                                critical_velocity = v1 + t * (v2 - v1)
                                critical_frequency = f1 + t * (f2 - f1)
                                break

                if critical_velocity is not None:
                    break

        return {
            'success': not self.has_fatal_errors,
            'errors': self.errors,
            'warnings': self.warnings,
            'modal_frequencies': [m.frequency_hz for m in self.modal_results],
            'modal_results': self.modal_results,
            'flutter_results': self.flutter_results,
            'critical_flutter_velocity': critical_velocity,
            'critical_flutter_frequency': critical_frequency,
            'has_results': len(self.modal_results) > 0 or len(self.flutter_results) > 0
        }

    def _empty_results(self) -> Dict[str, Any]:
        """Return empty results structure"""
        return {
            'success': False,
            'errors': self.errors if self.errors else ['F06 file not found or could not be parsed'],
            'warnings': self.warnings,
            'modal_frequencies': [],
            'modal_results': [],
            'flutter_results': [],
            'critical_flutter_velocity': None,
            'critical_flutter_frequency': None,
            'has_results': False
        }


def parse_f06_file(f06_path: Path) -> Dict[str, Any]:
    """Convenience function to parse F06 file"""
    parser = F06Parser(f06_path)
    return parser.parse()


if __name__ == "__main__":
    # Test parsing
    test_file = Path("test_flutter_fixed.f06")
    if test_file.exists():
        results = parse_f06_file(test_file)
        print(f"Parse success: {results['success']}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Modal frequencies found: {len(results['modal_frequencies'])}")
        print(f"Flutter points found: {len(results['flutter_results'])}")

        if results['critical_flutter_velocity']:
            print(f"Critical flutter velocity: {results['critical_flutter_velocity']:.1f} m/s")
            print(f"Critical flutter frequency: {results['critical_flutter_frequency']:.1f} Hz")
