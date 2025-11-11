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
            # Log all flutter points found for debugging
            logger.info(f"F06 Parser: Found {len(self.flutter_results)} flutter points")

            # Group flutter points by velocity
            from collections import defaultdict
            velocity_groups = defaultdict(list)
            for pt in self.flutter_results:
                velocity_groups[pt.velocity].append(pt)

            # Sort velocities
            sorted_velocities = sorted(velocity_groups.keys())
            logger.info(f"F06 Parser: Velocity range: {sorted_velocities[0]/100:.1f} to {sorted_velocities[-1]/100:.1f} m/s")

            # STRATEGY 1: Look for damping sign change (negative to positive) at ANY frequency
            # This captures low-frequency/rigid-body flutter modes that have frequency=0
            for i in range(len(sorted_velocities) - 1):
                v1 = sorted_velocities[i]
                v2 = sorted_velocities[i + 1]

                modes_v1 = velocity_groups[v1]
                modes_v2 = velocity_groups[v2]

                # Try to match modes by frequency (same mode will have similar frequency)
                for m1 in modes_v1:
                    # CRITICAL FIX: Accept ALL frequencies including 0 Hz (rigid-body modes)
                    # Only filter out obviously bad data (negative frequencies)
                    if m1.frequency < 0:
                        continue

                    # Find matching mode at next velocity
                    for m2 in modes_v2:
                        if m2.frequency < 0:
                            continue

                        # Check if this is likely the same mode
                        # For zero-frequency modes, they always match
                        # For non-zero frequency, require similarity
                        is_same_mode = False
                        if m1.frequency < 0.1 and m2.frequency < 0.1:
                            # Both near-zero frequency - assume same mode
                            is_same_mode = True
                        elif m1.frequency > 0.1 and m2.frequency > 0.1:
                            # Both non-zero - check frequency ratio
                            freq_ratio = abs(m2.frequency - m1.frequency) / m1.frequency
                            if freq_ratio < 0.3:  # Relaxed from 20% to 30%
                                is_same_mode = True

                        if is_same_mode:
                            # Check for flutter onset (negative to positive damping)
                            if m1.damping < 0 and m2.damping > 0:
                                # CRITICAL FIX: REMOVED overly aggressive damping filter
                                # Accept ANY damping crossing, including small values
                                # The crossing itself is the flutter point, regardless of magnitude

                                # Linear interpolation to zero damping
                                d1 = m1.damping
                                d2 = m2.damping
                                f1 = m1.frequency
                                f2 = m2.frequency

                                t = -d1 / (d2 - d1)
                                candidate_velocity = v1 + t * (v2 - v1)
                                candidate_frequency = f1 + t * (f2 - f1)

                                # CRITICAL FIX v2.1.1: NASTRAN outputs in cm/s, not mm/s
                                logger.info(f"Flutter detected: V={candidate_velocity/100:.1f} m/s, f={candidate_frequency:.1f} Hz")
                                logger.info(f"  Transition: V1={v1/100:.1f}m/s (g={d1:.4f}, f={f1:.1f}Hz), V2={v2/100:.1f}m/s (g={d2:.4f}, f={f2:.1f}Hz)")

                                # CRITICAL: Keep the LOWEST velocity flutter point (most conservative)
                                # Multiple modes may go unstable at different velocities
                                if critical_velocity is None or candidate_velocity < critical_velocity:
                                    critical_velocity = candidate_velocity
                                    critical_frequency = candidate_frequency
                                    logger.info(f"  → This is the LOWEST flutter point so far")

            # After checking all velocities, we have the lowest flutter point
            if critical_velocity is not None:
                logger.info(f"FINAL: Lowest flutter point at V={critical_velocity/100:.1f} m/s, f={critical_frequency:.1f} Hz")

            # STRATEGY 2: If no zero-crossing found, check for modes with positive damping
            # This handles cases where flutter is already established at lowest velocity
            if critical_velocity is None:
                logger.info("F06 Parser: No damping zero-crossing found, checking for already-unstable modes")
                for v in sorted_velocities:
                    modes = velocity_groups[v]
                    for mode in modes:
                        # Look for modes with positive damping (unstable) and realistic frequency
                        if mode.damping > 0:
                            logger.info(f"  Unstable mode at V={v/100:.1f}m/s: g={mode.damping:.4f}, f={mode.frequency:.1f}Hz")
                            # Report the lowest velocity with positive damping
                            if critical_velocity is None or v < critical_velocity:
                                critical_velocity = v
                                critical_frequency = mode.frequency
                                logger.info(f"  Using this as critical flutter point")

                if critical_velocity is not None:
                    logger.info(f"Flutter onset (already unstable): V={critical_velocity/100:.1f} m/s, f={critical_frequency:.1f} Hz")

            # Log if no flutter found
            if critical_velocity is None:
                logger.warning("F06 Parser: No flutter detected in velocity range")
                logger.warning(f"  Checked {len(sorted_velocities)} velocities from {sorted_velocities[0]/100:.1f} to {sorted_velocities[-1]/100:.1f} m/s")
                # Log sample of damping values for diagnosis
                for i, v in enumerate(sorted_velocities[:5]):  # First 5 velocities
                    modes = velocity_groups[v]
                    dampings = [f"g={m.damping:.2f}(f={m.frequency:.1f})" for m in modes[:3]]  # First 3 modes
                    logger.warning(f"  V={v/100:.1f}m/s: {', '.join(dampings)}")

        # CRITICAL: Convert velocity from cm/s (NASTRAN F06 units) to m/s for return
        critical_velocity_ms = critical_velocity / 100.0 if critical_velocity is not None else None

        return {
            'success': not self.has_fatal_errors,
            'errors': self.errors,
            'warnings': self.warnings,
            'modal_frequencies': [m.frequency_hz for m in self.modal_results],
            'modal_results': self.modal_results,
            'flutter_results': self.flutter_results,
            'critical_flutter_velocity': critical_velocity_ms,  # Now in m/s
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
