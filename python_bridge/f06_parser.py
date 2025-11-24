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

                        # CRITICAL FIX v2.1.9: Filter out rigid body/aerodynamic modes
                        # Lowered threshold from 0.1 Hz to 0.01 Hz to allow large panel low-frequency modes
                        # (10-second period modes are still physical for very large panels)
                        if frequency_hz > 0.01:  # Only keep modes above 0.01 Hz (down from 0.1 Hz)
                            self.modal_results.append(ModalResult(
                                mode_number=physical_mode_num,  # Renumber modes
                                frequency_hz=frequency_hz,
                                eigenvalue=eigenvalue,
                                generalized_mass=gen_mass,
                                generalized_stiffness=gen_stiff
                            ))
                            physical_mode_num += 1
                        else:
                            logger.debug(f"Filtered rigid body/aero mode {mode} with f={frequency_hz:.6f} Hz (<0.01 Hz)")
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Error parsing eigenvalue line: {line} - {e}")
                        continue

    def _parse_flutter_results(self):
        """Extract flutter analysis results from SOL 145"""
        # Look for flutter summary table with POINT information
        # Updated pattern to capture POINT header info
        flutter_pattern = r'FLUTTER\s+SUMMARY.*?POINT\s*=\s*(\d+)\s+MACH NUMBER\s*=\s*([\d.]+E?[+-]?\d*)\s+DENSITY RATIO\s*=\s*([\d.]+E?[+-]?\d*).*?\n(.*?)(?:\n1|\n0\s+FLUTTER|\Z)'
        matches = re.finditer(flutter_pattern, self.content, re.DOTALL)

        for match in matches:
            point_num = int(match.group(1))
            mach_number = float(match.group(2))
            density_ratio = float(match.group(3))
            table_text = match.group(4)

            # Log the POINT being parsed
            logger.info(f"Parsing FLUTTER SUMMARY POINT {point_num}: Mach={mach_number}, Density={density_ratio}")

            # Only parse POINT = 1 (primary analysis) to avoid confusion from multiple analysis points
            # Other points are parametric studies with different conditions
            if point_num == 1:
                self._parse_flutter_table(table_text, mach_number, density_ratio)
                break  # Only process the first POINT = 1

    def _parse_flutter_table(self, table_text: str, mach_number: float = 1.27, density_ratio: float = 0.5):
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

                    # CRITICAL FIX v2.14.1: Ensure proper parsing of negative damping
                    # F06 format sometimes has damping like "-1.2345E-01" or " -1.2345E-01"
                    damping_str = parts[3].strip()
                    damping = float(damping_str)

                    frequency = float(parts[4])
                    real_eigen = float(parts[5])
                    imag_eigen = float(parts[6]) if len(parts) > 6 else 0.0

                    # CRITICAL FIX v2.14.1: Enhanced debug for 139.4 m/s issue
                    if abs(velocity - 139394.0) < 1.0:  # 139394 mm/s = 139.4 m/s
                        logger.warning(f"DEBUG F06 PARSER at V=139394 (139.4 m/s):")
                        logger.warning(f"  Line: {line}")
                        logger.warning(f"  Parts: {parts}")
                        logger.warning(f"  Damping (parts[3]): '{parts[3]}' -> {damping}")
                        logger.warning(f"  Frequency: {frequency} Hz")
                        logger.warning(f"  Is damping positive? {damping > 0}")
                        if damping > 0:
                            logger.warning(f"  *** POSITIVE DAMPING DETECTED AT 139.4 m/s ***")

                    self.flutter_results.append(FlutterPoint(
                        velocity=velocity,
                        damping=damping,
                        frequency=frequency,
                        mach_number=mach_number,  # Use actual values from POINT header
                        density_ratio=density_ratio,  # Use actual values from POINT header
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
            logger.info(f"F06 Parser: Velocity range: {sorted_velocities[0]/1000:.1f} to {sorted_velocities[-1]/1000:.1f} m/s")

            # CRITICAL DEBUG v2.14.3: Show damping values at key velocities
            logger.warning("="*70)
            logger.warning("CRITICAL DEBUG: Damping values at key velocities")
            # Check velocities around flutter point
            test_velocities = [882222, 973000]  # Actual velocities from this run
            for v in sorted_velocities:
                if v >= 850000 and v <= 1000000:  # Around flutter region
                    modes = velocity_groups[v]
                    logger.warning(f"V={v/1000:.1f} m/s:")
                    for m in modes[:3]:  # First 3 modes
                        logger.warning(f"  f={m.frequency:.1f} Hz, g={m.damping:.6f}")
            logger.warning("="*70)

            # STRATEGY 1: Look for damping sign change (negative to positive) at ANY frequency
            # This captures low-frequency/rigid-body flutter modes that have frequency=0
            for i in range(len(sorted_velocities) - 1):
                v1 = sorted_velocities[i]
                v2 = sorted_velocities[i + 1]

                modes_v1 = velocity_groups[v1]
                modes_v2 = velocity_groups[v2]

                # Try to match modes by frequency (same mode will have similar frequency)
                for m1 in modes_v1:
                    # CRITICAL FIX v2.2.0: Reject KFREQ=0 modes (divergence, not flutter)
                    # Flutter requires oscillating modes (frequency > 0)
                    # KFREQ=0 means zero reduced frequency = divergence or numerical artifact
                    if m1.frequency <= 0.01:  # Small threshold to handle numerical noise
                        continue

                    # Find matching mode at next velocity
                    for m2 in modes_v2:
                        if m2.frequency <= 0.01:
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

                        # CRITICAL DEBUG v2.14.3: Log mode matching attempts
                        if v1 == 882222 and v2 == 973000 and m1.frequency > 100 and m1.frequency < 120:
                            logger.warning(f"DEBUG MODE MATCH: V1={v1/1000:.1f}, V2={v2/1000:.1f}")
                            logger.warning(f"  m1: f={m1.frequency:.2f} Hz, g={m1.damping:.6f}")
                            logger.warning(f"  m2: f={m2.frequency:.2f} Hz, g={m2.damping:.6f}")
                            logger.warning(f"  freq_ratio={(abs(m2.frequency - m1.frequency) / m1.frequency):.3f}")
                            logger.warning(f"  is_same_mode={is_same_mode}")

                        if is_same_mode:
                            # Check for flutter onset (negative to positive damping)
                            # CRITICAL FIX v2.14.4: Filter numerical noise - damping must be clearly positive
                            # Values like 1E-4 (0.0001) are numerical noise, not real positive damping
                            # Real flutter typically has damping > 0.0001 (1E-4)
                            # CRITICAL FIX v2.17.0: Filter unrealistic damping values
                            # Damping > 10.0 is clearly spurious
                            # NOTE: Relaxed upper limit from 1.0 to 10.0 for high-energy flutter modes
                            if m1.damping < 0 and m2.damping > 0.0001 and m2.damping < 10.0:
                                # CRITICAL FIX v2.14.1: Log detected crossings
                                logger.info(f"DETECTED DAMPING CROSSING:")
                                logger.info(f"  V1={v1/1000:.1f} m/s: g={m1.damping:.6f}, f={m1.frequency:.1f} Hz")
                                logger.info(f"  V2={v2/1000:.1f} m/s: g={m2.damping:.6f}, f={m2.frequency:.1f} Hz")
                                # CRITICAL FIX: REMOVED overly aggressive damping filter
                                # Accept ANY damping crossing, including small values
                                # The crossing itself is the flutter point, regardless of magnitude

                                # Linear interpolation to zero damping
                                d1 = m1.damping
                                d2 = m2.damping
                                f1 = m1.frequency
                                f2 = m2.frequency

                                # CRITICAL FIX v2.1.9: Validate interpolation to prevent numerical issues
                                # Check for near-zero damping gradient (division by zero)
                                if abs(d2 - d1) < 1e-10:
                                    logger.debug(f"Skipping near-zero damping gradient at V={v1/1000:.1f}m/s (Δg={d2-d1:.2e})")
                                    continue

                                t = -d1 / (d2 - d1)

                                # Validate interpolation parameter (should be in [0,1] for true interpolation)
                                # Allow 10% extrapolation for robustness, but warn if excessive
                                if not (-0.1 <= t <= 1.1):
                                    logger.warning(f"Interpolation out of bounds: t={t:.3f} at V={v1/1000:.1f}m/s, skipping")
                                    continue

                                candidate_velocity = v1 + t * (v2 - v1)
                                candidate_frequency = f1 + t * (f2 - f1)

                                # Validate physical results (positive velocity and frequency)
                                if candidate_velocity <= 0 or candidate_frequency <= 0:
                                    logger.warning(f"Non-physical flutter point: V={candidate_velocity/1000:.1f}m/s, f={candidate_frequency:.1f}Hz, skipping")
                                    continue

                                # CRITICAL FIX v2.1.9: NASTRAN F06 velocities in mm/s (not cm/s)
                                logger.info(f"Flutter detected: V={candidate_velocity/1000:.1f} m/s, f={candidate_frequency:.1f} Hz")
                                logger.info(f"  Transition: V1={v1/1000:.1f}m/s (g={d1:.4f}, f={f1:.1f}Hz), V2={v2/1000:.1f}m/s (g={d2:.4f}, f={f2:.1f}Hz)")

                                # CRITICAL FIX v2.14.4: Additional validation - verify positive damping exists
                                # Check that at least one of the velocities has actual positive damping
                                # (not just interpolation between two negative values or numerical noise)
                                # NOTE: Relaxed threshold to 0.0001 as some panels have small damping values at flutter
                                if d2 <= 0.0001:  # Relaxed from 0.001 to 0.0001 for sensitive detection
                                    logger.warning(f"FALSE CROSSING: d2={d2:.6e} is not clearly positive (noise)")
                                    logger.warning(f"  d1={d1:.6f}, d2={d2:.6e} - This is NOT flutter - skipping")
                                    continue

                                # CRITICAL FIX v2.16.0: Filter out flutter at minimum velocity
                                # If flutter is detected very close to the minimum velocity, it's likely
                                # a false positive due to starting the analysis in an already-transitioning region
                                min_velocity = sorted_velocities[0]  # First velocity in the sweep
                                if candidate_velocity < min_velocity * 1.2:  # Within 1.2x of minimum (relaxed from 2.5x)
                                    logger.warning(f"REJECTING FLUTTER at {candidate_velocity/1000:.1f} m/s - too close to minimum velocity {min_velocity/1000:.1f} m/s")
                                    logger.warning(f"  This is likely a false positive from starting analysis in transition region")
                                    continue

                                # CRITICAL: Keep the LOWEST velocity flutter point (most conservative)
                                # Multiple modes may go unstable at different velocities
                                if critical_velocity is None or candidate_velocity < critical_velocity:
                                    critical_velocity = candidate_velocity
                                    critical_frequency = candidate_frequency
                                    logger.info(f"  → This is the LOWEST flutter point so far")

            # After checking all velocities, we have the lowest flutter point
            if critical_velocity is not None:
                logger.info(f"FINAL: Lowest flutter point at V={critical_velocity/1000:.1f} m/s, f={critical_frequency:.1f} Hz")

            # STRATEGY 2: If no zero-crossing found, check for modes with positive damping
            # This handles cases where flutter is already established at lowest velocity
            if critical_velocity is None:
                logger.info("F06 Parser: No damping zero-crossing found, checking for already-unstable modes")

                # Find the first velocity with any unstable modes
                for v in sorted_velocities:
                    modes = velocity_groups[v]
                    unstable_modes = []

                    for mode in modes:
                        # CRITICAL FIX v2.2.0: Skip KFREQ=0 modes (divergence, not flutter)
                        if mode.frequency <= 0.01:
                            continue

                        # CRITICAL FIX v2.14.4: Properly filter numerical noise
                        # Look for modes with clearly positive damping (unstable) and realistic frequency
                        # Filter out very low frequency modes (<1 Hz) which may be rigid body or spurious
                        # CRITICAL: Damping must be > 0.0001 to avoid numerical noise (e.g., 1E-5)
                        # Real flutter has damping typically > 0.0001 (not 1E-5 which is noise)
                        # NOTE: Relaxed frequency and damping thresholds for sensitive detection
                        if mode.damping > 0.0001 and mode.frequency >= 1.0:
                            unstable_modes.append(mode)
                            logger.info(f"  Unstable mode at V={v/1000:.1f}m/s: g={mode.damping:.4f}, f={mode.frequency:.1f}Hz")

                    # If we found unstable modes at this velocity, select the MOST unstable one
                    if unstable_modes:
                        # Select mode with highest positive damping (most unstable)
                        most_unstable = max(unstable_modes, key=lambda m: m.damping)
                        critical_velocity = v
                        critical_frequency = most_unstable.frequency
                        logger.info(f"  *** Selected MOST UNSTABLE mode: g={most_unstable.damping:.4f}, f={most_unstable.frequency:.1f}Hz")
                        logger.info(f"  Using this as critical flutter point")
                        break  # Stop at first velocity with unstable modes

                if critical_velocity is not None:
                    logger.info(f"Flutter onset (already unstable): V={critical_velocity/1000:.1f} m/s, f={critical_frequency:.1f} Hz")

            # Log if no flutter found
            if critical_velocity is None:
                logger.warning("F06 Parser: No flutter detected in velocity range")
                logger.warning(f"  Checked {len(sorted_velocities)} velocities from {sorted_velocities[0]/1000:.1f} to {sorted_velocities[-1]/1000:.1f} m/s")
                # Log sample of damping values for diagnosis
                for i, v in enumerate(sorted_velocities[:5]):  # First 5 velocities
                    modes = velocity_groups[v]
                    dampings = [f"g={m.damping:.2f}(f={m.frequency:.1f})" for m in modes[:3]]  # First 3 modes
                    logger.warning(f"  V={v/1000:.1f}m/s: {', '.join(dampings)}")

        # CRITICAL FIX v2.1.9: Convert velocity from mm/s (NASTRAN F06 units) to m/s for return
        # NASTRAN uses mm-kg-s-N unit system, so FLFACT velocities and F06 output are in mm/s
        critical_velocity_ms = critical_velocity / 1000.0 if critical_velocity is not None else None

        # CRITICAL FIX v2.2.0: Only report flutter if actually found (not false crossing from negative dampings)
        flutter_found = critical_velocity is not None

        # Additional check: If we found a velocity, verify it's from actual positive damping
        # (not just interpolation between two negative values)
        if critical_velocity is not None:
            # Check if any mode at any velocity has positive damping
            has_positive_damping = False
            for v in sorted_velocities:
                for mode in velocity_groups[v]:
                    if mode.damping > 0.0001:  # Relaxed threshold from 0.001 to 0.0001 for sensitive detection
                        has_positive_damping = True
                        break
                if has_positive_damping:
                    break

            if not has_positive_damping:
                logger.warning("=" * 70)
                logger.warning("⚠️  FALSE FLUTTER DETECTION")
                logger.warning("=" * 70)
                logger.warning(f"Found interpolated crossing at {critical_velocity_ms:.1f} m/s")
                logger.warning("BUT all dampings are NEGATIVE (no actual flutter)")
                logger.warning("This means panel is STABLE across entire velocity range")
                logger.warning(f"Tested range: {sorted_velocities[0]/1000:.1f} to {sorted_velocities[-1]/1000:.1f} m/s")
                logger.warning("RECOMMENDATION: Flutter speed is ABOVE maximum tested velocity")
                logger.warning("=" * 70)

                # Clear the false positive
                critical_velocity_ms = None
                critical_frequency = None
                flutter_found = False

        return {
            'success': not self.has_fatal_errors,
            'errors': self.errors,
            'warnings': self.warnings,
            'modal_frequencies': [m.frequency_hz for m in self.modal_results],
            'modal_results': self.modal_results,
            'flutter_results': self.flutter_results,
            'critical_flutter_velocity': critical_velocity_ms,  # Now in m/s (or None if false positive)
            'critical_flutter_frequency': critical_frequency,
            'flutter_found': flutter_found,  # NEW: Explicit flag
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
            'flutter_found': False,
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
