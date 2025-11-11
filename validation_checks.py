"""
VALIDATION CHECKS MODULE
========================
Runtime validation functions for ensuring physical correctness and safety.

These functions should be called before returning results to the user to catch:
- Non-physical values (negative speeds, frequencies)
- Unit conversion errors
- Out-of-range parameters
- Unreliable predictions

Author: Aeroelasticity Expert
Date: 2025-11-11
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_material_properties(youngs_modulus: float, poissons_ratio: float,
                                 density: float, thickness: float) -> Tuple[bool, List[str]]:
    """
    Validate material properties are physical and reasonable.

    Args:
        youngs_modulus: Young's modulus (Pa)
        poissons_ratio: Poisson's ratio (dimensionless)
        density: Material density (kg/m³)
        thickness: Panel thickness (m)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Young's modulus checks
    if youngs_modulus <= 0:
        errors.append(f"Invalid Young's modulus: {youngs_modulus} Pa (must be positive)")
    elif youngs_modulus < 1e9:  # < 1 GPa
        errors.append(f"WARNING: Young's modulus {youngs_modulus/1e9:.1f} GPa is very low (< 1 GPa). Check units.")
    elif youngs_modulus > 1000e9:  # > 1000 GPa
        errors.append(f"WARNING: Young's modulus {youngs_modulus/1e9:.1f} GPa is very high (> 1000 GPa). Check units.")

    # Typical aerospace materials: 10-500 GPa
    if 10e9 <= youngs_modulus <= 500e9:
        logger.debug(f"Young's modulus {youngs_modulus/1e9:.1f} GPa is reasonable")

    # Poisson's ratio checks
    if poissons_ratio <= -1 or poissons_ratio >= 0.5:
        errors.append(f"Invalid Poisson's ratio: {poissons_ratio} (must be -1 < ν < 0.5)")
    elif poissons_ratio < 0:
        errors.append(f"WARNING: Negative Poisson's ratio {poissons_ratio} (auxetic material)")

    # Typical aerospace materials: 0.25-0.35
    if 0.20 <= poissons_ratio <= 0.40:
        logger.debug(f"Poisson's ratio {poissons_ratio:.2f} is reasonable")

    # Density checks
    if density <= 0:
        errors.append(f"Invalid density: {density} kg/m³ (must be positive)")
    elif density < 100:  # < 100 kg/m³ (foam)
        errors.append(f"WARNING: Density {density} kg/m³ is very low. Foam/honeycomb core?")
    elif density > 20000:  # > 20000 kg/m³ (heavier than tungsten)
        errors.append(f"WARNING: Density {density} kg/m³ is very high (> tungsten). Check units.")

    # Typical aerospace materials: 1000-8000 kg/m³
    if 1000 <= density <= 10000:
        logger.debug(f"Density {density} kg/m³ is reasonable")

    # Thickness checks
    if thickness <= 0:
        errors.append(f"Invalid thickness: {thickness} m (must be positive)")
    elif thickness < 0.0001:  # < 0.1 mm
        errors.append(f"WARNING: Thickness {thickness*1000:.3f} mm is very thin. Check units.")
    elif thickness > 0.1:  # > 100 mm
        errors.append(f"WARNING: Thickness {thickness*1000:.1f} mm is very thick. Check units.")

    # Typical aerospace panels: 0.5-10 mm
    if 0.0005 <= thickness <= 0.02:
        logger.debug(f"Thickness {thickness*1000:.1f} mm is reasonable")

    is_valid = len([e for e in errors if not e.startswith("WARNING")]) == 0

    return is_valid, errors


def validate_geometry(length: float, width: float, thickness: float) -> Tuple[bool, List[str]]:
    """
    Validate panel geometry is physical and reasonable.

    Args:
        length: Panel length (m)
        width: Panel width (m)
        thickness: Panel thickness (m)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Dimension checks
    if length <= 0:
        errors.append(f"Invalid length: {length} m (must be positive)")
    if width <= 0:
        errors.append(f"Invalid width: {width} m (must be positive)")
    if thickness <= 0:
        errors.append(f"Invalid thickness: {thickness} m (must be positive)")

    # Aspect ratio check
    if length > 0 and width > 0:
        aspect_ratio = length / width
        if aspect_ratio > 10:
            errors.append(f"WARNING: High aspect ratio {aspect_ratio:.1f} (>10). May violate plate theory assumptions.")
        elif aspect_ratio < 0.1:
            errors.append(f"WARNING: Low aspect ratio {aspect_ratio:.2f} (<0.1). May violate plate theory assumptions.")

    # Thickness ratio check (classical plate theory valid for t/L < 0.05)
    if length > 0 and thickness > 0:
        thickness_ratio = thickness / length
        if thickness_ratio > 0.05:
            errors.append(f"WARNING: Thickness ratio {thickness_ratio:.3f} > 0.05. Classical plate theory may be inaccurate.")
        elif thickness_ratio < 0.0001:
            errors.append(f"WARNING: Thickness ratio {thickness_ratio:.4f} < 0.0001. Very thin membrane.")

    # Size reasonableness
    if length > 10:
        errors.append(f"WARNING: Length {length} m is very large (>10m). Check units.")
    if width > 10:
        errors.append(f"WARNING: Width {width} m is very large (>10m). Check units.")

    is_valid = len([e for e in errors if not e.startswith("WARNING")]) == 0

    return is_valid, errors


def validate_flow_conditions(mach_number: float, altitude: float,
                            temperature: float, density: float) -> Tuple[bool, List[str]]:
    """
    Validate flow conditions are physical and reasonable.

    Args:
        mach_number: Mach number (dimensionless)
        altitude: Altitude (m)
        temperature: Static temperature (K)
        density: Air density (kg/m³)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Mach number checks
    if mach_number <= 0:
        errors.append(f"Invalid Mach number: {mach_number} (must be positive)")
    elif mach_number > 10:
        errors.append(f"WARNING: Mach {mach_number} > 10 (hypersonic). Analysis may be inaccurate.")

    # Altitude checks
    if altitude < 0:
        errors.append(f"Invalid altitude: {altitude} m (must be non-negative)")
    elif altitude > 100000:
        errors.append(f"WARNING: Altitude {altitude/1000:.1f} km > 100 km. ISA model may be inaccurate.")

    # Temperature checks
    if temperature <= 0:
        errors.append(f"Invalid temperature: {temperature} K (must be positive)")
    elif temperature < 150:
        errors.append(f"WARNING: Temperature {temperature} K < 150 K. Very cold.")
    elif temperature > 500:
        errors.append(f"WARNING: Temperature {temperature} K > 500 K. Very hot.")

    # Typical atmosphere: 200-300 K
    if 200 <= temperature <= 300:
        logger.debug(f"Temperature {temperature} K is reasonable")

    # Density checks
    if density <= 0:
        errors.append(f"Invalid density: {density} kg/m³ (must be positive)")
    elif density > 2.0:
        errors.append(f"WARNING: Air density {density} kg/m³ > 2.0 (sea level ≈ 1.225). Check units.")

    # ISA consistency check
    if 0 <= altitude <= 100000 and temperature > 0:
        # Approximate ISA density
        if altitude < 11000:
            T_isa = 288.15 - 0.0065 * altitude
            P_isa = 101325 * (1 - 0.0065 * altitude / 288.15)**5.256
        else:
            T_isa = 216.65
            P_isa = 22632 * np.exp(-(altitude - 11000) / 6341.6)

        rho_isa = P_isa / (287.0 * T_isa)

        if abs(density - rho_isa) / rho_isa > 0.5:
            errors.append(f"WARNING: Density {density:.3f} deviates >50% from ISA ({rho_isa:.3f} kg/m³)")

    is_valid = len([e for e in errors if not e.startswith("WARNING")]) == 0

    return is_valid, errors


def validate_flutter_results(flutter_speed: float, flutter_frequency: float,
                            flutter_mode: int, converged: bool,
                            mach_number: float, speed_of_sound: float) -> Tuple[bool, List[str]]:
    """
    Validate flutter analysis results are physical and reliable.

    Args:
        flutter_speed: Critical flutter speed (m/s)
        flutter_frequency: Flutter frequency (Hz)
        flutter_mode: Flutter mode number
        converged: Convergence status
        mach_number: Flow Mach number
        speed_of_sound: Speed of sound (m/s)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Flutter speed checks
    if flutter_speed <= 0:
        errors.append(f"Invalid flutter speed: {flutter_speed} m/s (must be positive)")
    elif flutter_speed > 10 * speed_of_sound:
        errors.append(f"WARNING: Flutter speed {flutter_speed:.0f} m/s exceeds Mach 10. Unrealistic.")
    elif flutter_speed == 9999.0:
        errors.append(f"WARNING: Flutter speed is placeholder value (9999). No flutter found in range.")

    # Flutter frequency checks
    if flutter_frequency < 0:
        errors.append(f"Invalid flutter frequency: {flutter_frequency} Hz (must be non-negative)")
    elif flutter_frequency == 0:
        errors.append(f"WARNING: Zero flutter frequency. Possible divergence instability.")
    elif flutter_frequency > 1000:
        errors.append(f"WARNING: Flutter frequency {flutter_frequency:.0f} Hz > 1000 Hz. Very high.")

    # Mode number check
    if flutter_mode <= 0:
        errors.append(f"Invalid flutter mode: {flutter_mode} (must be positive integer)")

    # Convergence check
    if not converged:
        errors.append(f"WARNING: Flutter analysis did not converge. Results may be unreliable.")

    # Cross-checks
    if flutter_speed > 0 and speed_of_sound > 0:
        flutter_mach = flutter_speed / speed_of_sound
        if flutter_mach < mach_number * 0.5:
            errors.append(f"WARNING: Flutter Mach {flutter_mach:.2f} < 0.5×flow Mach {mach_number:.2f}. Unusual.")

    is_valid = len([e for e in errors if not e.startswith("WARNING")]) == 0

    return is_valid, errors


def validate_units_consistency(values: Dict[str, float],
                              expected_units: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that numerical values are consistent with expected unit ranges.

    Args:
        values: Dictionary of {parameter_name: value}
        expected_units: Dictionary of {parameter_name: unit_string}

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Unit range checks
    unit_ranges = {
        'Pa': (1e6, 1e12),       # 1 MPa to 1000 GPa
        'MPa': (1, 1e6),         # 1 MPa to 1000 GPa
        'GPa': (0.001, 1000),    # 1 MPa to 1000 GPa
        'm': (0.0001, 100),      # 0.1 mm to 100 m
        'mm': (0.1, 100000),     # 0.1 mm to 100 m
        'kg/m³': (10, 25000),    # 10 to 25000 kg/m³
        'kg/mm³': (1e-11, 1e-5), # 10 to 25000 kg/m³ in mm units
        'm/s': (0.1, 10000),     # 0.1 to 10000 m/s
        'cm/s': (10, 1000000),   # 0.1 to 10000 m/s in cm
        'Hz': (0.01, 10000),     # 0.01 to 10000 Hz
        'K': (100, 1000),        # 100 to 1000 K
    }

    for param, value in values.items():
        if param in expected_units:
            unit = expected_units[param]
            if unit in unit_ranges:
                min_val, max_val = unit_ranges[unit]
                if value < min_val or value > max_val:
                    errors.append(f"WARNING: {param}={value} {unit} outside typical range "
                                f"[{min_val}, {max_val}]. Check units.")

    is_valid = len([e for e in errors if not e.startswith("WARNING")]) == 0

    return is_valid, errors


def comprehensive_validation_check(panel_props: Dict, flow_props: Dict,
                                   flutter_result: Dict) -> Dict[str, any]:
    """
    Perform comprehensive validation of entire analysis.

    Args:
        panel_props: Panel properties dictionary
        flow_props: Flow conditions dictionary
        flutter_result: Flutter analysis result dictionary

    Returns:
        Validation report dictionary
    """
    report = {
        'overall_valid': True,
        'errors': [],
        'warnings': [],
        'checks_performed': []
    }

    # Check 1: Material properties
    mat_valid, mat_errors = validate_material_properties(
        panel_props.get('youngs_modulus', 0),
        panel_props.get('poissons_ratio', 0),
        panel_props.get('density', 0),
        panel_props.get('thickness', 0)
    )
    report['checks_performed'].append('material_properties')
    if not mat_valid:
        report['overall_valid'] = False
    for err in mat_errors:
        if err.startswith('WARNING'):
            report['warnings'].append(err)
        else:
            report['errors'].append(err)

    # Check 2: Geometry
    geom_valid, geom_errors = validate_geometry(
        panel_props.get('length', 0),
        panel_props.get('width', 0),
        panel_props.get('thickness', 0)
    )
    report['checks_performed'].append('geometry')
    if not geom_valid:
        report['overall_valid'] = False
    for err in geom_errors:
        if err.startswith('WARNING'):
            report['warnings'].append(err)
        else:
            report['errors'].append(err)

    # Check 3: Flow conditions
    flow_valid, flow_errors = validate_flow_conditions(
        flow_props.get('mach_number', 0),
        flow_props.get('altitude', 0),
        flow_props.get('temperature', 288.15),
        flow_props.get('density', 1.225)
    )
    report['checks_performed'].append('flow_conditions')
    if not flow_valid:
        report['overall_valid'] = False
    for err in flow_errors:
        if err.startswith('WARNING'):
            report['warnings'].append(err)
        else:
            report['errors'].append(err)

    # Check 4: Flutter results
    flutter_valid, flutter_errors = validate_flutter_results(
        flutter_result.get('flutter_speed', 0),
        flutter_result.get('flutter_frequency', 0),
        flutter_result.get('flutter_mode', 0),
        flutter_result.get('converged', False),
        flow_props.get('mach_number', 0),
        flow_props.get('speed_of_sound', 340)
    )
    report['checks_performed'].append('flutter_results')
    if not flutter_valid:
        report['overall_valid'] = False
    for err in flutter_errors:
        if err.startswith('WARNING'):
            report['warnings'].append(err)
        else:
            report['errors'].append(err)

    # Summary
    report['error_count'] = len(report['errors'])
    report['warning_count'] = len(report['warnings'])

    if report['error_count'] > 0:
        logger.error(f"Validation FAILED: {report['error_count']} errors found")
    elif report['warning_count'] > 0:
        logger.warning(f"Validation WARNING: {report['warning_count']} warnings found")
    else:
        logger.info("Validation PASSED: No issues found")

    return report


if __name__ == "__main__":
    # Test validation functions
    import sys

    print("Testing validation functions...")
    print("="*60)

    # Test 1: Valid material
    print("\nTest 1: Valid aluminum material")
    valid, errors = validate_material_properties(71.7e9, 0.33, 2810, 0.0015)
    print(f"Valid: {valid}")
    for err in errors:
        print(f"  {err}")

    # Test 2: Invalid units (MPa instead of Pa)
    print("\nTest 2: Invalid Young's modulus (wrong units)")
    valid, errors = validate_material_properties(71.7, 0.33, 2810, 0.0015)
    print(f"Valid: {valid}")
    for err in errors:
        print(f"  {err}")

    # Test 3: Valid geometry
    print("\nTest 3: Valid panel geometry")
    valid, errors = validate_geometry(0.3, 0.3, 0.0015)
    print(f"Valid: {valid}")
    for err in errors:
        print(f"  {err}")

    # Test 4: Valid flow
    print("\nTest 4: Valid flow conditions")
    valid, errors = validate_flow_conditions(2.0, 10000, 223, 0.41)
    print(f"Valid: {valid}")
    for err in errors:
        print(f"  {err}")

    # Test 5: Invalid flutter result
    print("\nTest 5: Invalid flutter result (non-converged)")
    valid, errors = validate_flutter_results(1500, 50, 1, False, 2.0, 295)
    print(f"Valid: {valid}")
    for err in errors:
        print(f"  {err}")

    print("\n" + "="*60)
    print("Validation functions test complete")
