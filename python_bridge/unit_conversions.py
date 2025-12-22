"""
NASTRAN Unit System Conversions
==============================================
CRITICAL: These conversions are used for flight safety calculations

TWO NASTRAN UNIT SYSTEMS:
========================

1. mm-kg-s-N (documented in this module):
   - Length: millimeters (mm)
   - Mass: kilograms (kg)
   - Time: seconds (s)
   - Force: 0.001 N (NOT force-consistent!)
   - Density: kg/mm^3 = kg/m^3 × 1e-9

2. mm-tonne-s-N (used by BDF generators):
   - Length: millimeters (mm)
   - Mass: tonnes (Mg = 1000 kg)
   - Time: seconds (s)
   - Force: N (force-consistent: F = ma = 1 tonne × 1 mm/s² = 1 N)
   - Density: tonne/mm^3 = kg/m^3 × 1e-12
   - Modulus: MPa = N/mm²

IMPORTANT: The BDF generators (simple_bdf_generator.py, bdf_generator_sol145_fixed.py)
use mm-tonne-s-N system for force consistency with E in MPa.
The functions in this module use mm-kg-s-N for legacy compatibility.

For BDF generation, use:
- Material density: kg/m³ × 1e-12 → tonne/mm³
- Air density: kg/m³ × 1e-12 → tonne/mm³

Derived Units (mm-kg-s-N):
- Stress/Pressure: N/mm^2 = MPa
- Density: kg/mm^3
- Velocity: mm/s
"""


def density_si_to_nastran(density_kg_m3: float) -> float:
    """
    Convert density from SI (kg/m^3) to NASTRAN mm-kg-s-N (kg/mm^3)

    Args:
        density_kg_m3: Density in kg/m^3 (e.g., 2810 for aluminum)

    Returns:
        Density in kg/mm^3 (e.g., 2.81e-9 for aluminum)

    Examples:
        >>> density_si_to_nastran(2810)  # Aluminum
        2.81e-09
        >>> density_si_to_nastran(7850)  # Steel
        7.85e-09

    CRITICAL SAFETY NOTE:
    1 m = 1000 mm, therefore 1 m^3 = (1000 mm)^3 = 10⁹ mm^3 (NOT 10⁶!)
    Error in conversion factor has 1000× safety impact on flutter predictions.

    Conversion formula:
    ρ[kg/mm^3] = ρ[kg/m^3] × (1 m^3 / 10⁹ mm^3) = ρ[kg/m^3] × 10⁻⁹
    """
    return density_kg_m3 * 1e-9  # kg/m^3 × (1 m^3 / 10⁹ mm^3) = kg/mm^3


def density_nastran_to_si(density_kg_mm3: float) -> float:
    """
    Convert density from NASTRAN mm-kg-s-N (kg/mm^3) to SI (kg/m^3)

    Args:
        density_kg_mm3: Density in kg/mm^3 (e.g., 2.81e-9 for aluminum)

    Returns:
        Density in kg/m^3 (e.g., 2810 for aluminum)

    Examples:
        >>> density_nastran_to_si(2.81e-9)
        2810.0
        >>> density_nastran_to_si(7.85e-9)
        7850.0

    Conversion formula:
    ρ[kg/m^3] = ρ[kg/mm^3] × (10⁹ mm^3 / 1 m^3) = ρ[kg/mm^3] × 10⁹
    """
    return density_kg_mm3 * 1e9  # kg/mm^3 × (10⁹ mm^3 / 1 m^3) = kg/m^3


def density_si_to_nastran_tonne(density_kg_m3: float) -> float:
    """
    Convert density from SI (kg/m^3) to NASTRAN mm-tonne-s-N (tonne/mm^3)

    This is the preferred conversion for BDF generation where E is in MPa.
    Use this for both material density and air density to maintain consistency.

    Args:
        density_kg_m3: Density in kg/m^3 (e.g., 2810 for aluminum)

    Returns:
        Density in tonne/mm^3 (e.g., 2.81e-9 for aluminum)

    Examples:
        >>> density_si_to_nastran_tonne(2810)  # Aluminum
        2.81e-09
        >>> density_si_to_nastran_tonne(1.225)  # Air at sea level
        1.225e-12

    CRITICAL SAFETY NOTE:
    1 tonne = 1000 kg, and 1 m^3 = 10^9 mm^3
    Factor = (1 tonne / 1000 kg) × (1 m^3 / 10^9 mm^3) = 10^-3 × 10^-9 = 10^-12

    Conversion formula:
    ρ[tonne/mm^3] = ρ[kg/m^3] × 10^-12
    """
    return density_kg_m3 * 1e-12  # kg/m^3 → tonne/mm^3


def density_nastran_tonne_to_si(density_tonne_mm3: float) -> float:
    """
    Convert density from NASTRAN mm-tonne-s-N (tonne/mm^3) to SI (kg/m^3)

    Args:
        density_tonne_mm3: Density in tonne/mm^3 (e.g., 2.81e-9 for aluminum)

    Returns:
        Density in kg/m^3 (e.g., 2810 for aluminum)

    Examples:
        >>> density_nastran_tonne_to_si(2.81e-9)
        2810.0
        >>> density_nastran_tonne_to_si(1.225e-12)
        1.225

    Conversion formula:
    ρ[kg/m^3] = ρ[tonne/mm^3] × 10^12
    """
    return density_tonne_mm3 * 1e12  # tonne/mm^3 → kg/m^3


def velocity_si_to_nastran(velocity_m_s: float) -> float:
    """
    Convert velocity from SI (m/s) to NASTRAN mm-kg-s-N (mm/s)

    Args:
        velocity_m_s: Velocity in m/s (e.g., 272 for Mach 0.8 at sea level)

    Returns:
        Velocity in mm/s (e.g., 272000 for Mach 0.8)

    Examples:
        >>> velocity_si_to_nastran(100)  # 100 m/s
        100000.0
        >>> velocity_si_to_nastran(340)  # Speed of sound at sea level
        340000.0

    Conversion formula:
    V[mm/s] = V[m/s] × (1000 mm / 1 m) = V[m/s] × 10^3
    """
    return velocity_m_s * 1e3  # m/s × (1000 mm / 1 m) = mm/s


def velocity_nastran_to_si(velocity_mm_s: float) -> float:
    """
    Convert velocity from NASTRAN mm-kg-s-N (mm/s) to SI (m/s)

    Args:
        velocity_mm_s: Velocity in mm/s (e.g., 272000 for Mach 0.8)

    Returns:
        Velocity in m/s (e.g., 272 for Mach 0.8)

    Examples:
        >>> velocity_nastran_to_si(100000)
        100.0
        >>> velocity_nastran_to_si(340000)
        340.0

    Conversion formula:
    V[m/s] = V[mm/s] × (1 m / 1000 mm) = V[mm/s] × 10⁻^3
    """
    return velocity_mm_s * 1e-3  # mm/s × (1 m / 1000 mm) = m/s


def stress_si_to_nastran(stress_pa: float) -> float:
    """
    Convert stress/pressure from SI (Pa) to NASTRAN mm-kg-s-N (N/mm^2 = MPa)

    Args:
        stress_pa: Stress in Pa (e.g., 71.7e9 Pa = 71.7 GPa for aluminum)

    Returns:
        Stress in N/mm^2 = MPa (e.g., 71700 MPa for aluminum)

    Examples:
        >>> stress_si_to_nastran(71.7e9)  # Aluminum Young's modulus
        71700.0
        >>> stress_si_to_nastran(200e9)  # Steel Young's modulus
        200000.0

    Conversion formula:
    σ[N/mm^2] = σ[Pa] × (1 Pa / 1 N/m^2) × (1 m^2 / 10⁶ mm^2) = σ[Pa] × 10⁻⁶
    """
    return stress_pa * 1e-6  # Pa × (1 m^2 / 10⁶ mm^2) = N/mm^2 = MPa


def stress_nastran_to_si(stress_mpa: float) -> float:
    """
    Convert stress/pressure from NASTRAN mm-kg-s-N (N/mm^2 = MPa) to SI (Pa)

    Args:
        stress_mpa: Stress in N/mm^2 = MPa (e.g., 71700 for aluminum)

    Returns:
        Stress in Pa (e.g., 71.7e9 Pa for aluminum)

    Examples:
        >>> stress_nastran_to_si(71700)
        71700000000.0
        >>> stress_nastran_to_si(200000)
        200000000000.0

    Conversion formula:
    σ[Pa] = σ[N/mm^2] × (10⁶ mm^2 / 1 m^2) = σ[MPa] × 10⁶
    """
    return stress_mpa * 1e6  # N/mm^2 × (10⁶ mm^2 / 1 m^2) = Pa


# Unit conversion validation
def validate_conversions():
    """Validate unit conversions with known materials and conditions"""

    print("NASTRAN Unit Conversion Validation")
    print("=" * 70)

    test_materials = [
        ("Aluminum 6061", 2810, 2.81e-9),
        ("Steel 4130", 7850, 7.85e-9),
        ("Titanium Ti-6Al-4V", 4430, 4.43e-9),
        ("Carbon Fiber/Epoxy", 1570, 1.57e-9),
    ]

    print("\n1. Density Conversions (kg/m^3 -> kg/mm^3)")
    print("-" * 70)
    all_passed = True

    for name, rho_si, rho_nastran_expected in test_materials:
        rho_nastran_calc = density_si_to_nastran(rho_si)
        error = abs(rho_nastran_calc - rho_nastran_expected) / rho_nastran_expected

        status = "[PASS]" if error < 0.01 else "[FAIL]"
        print(f"{status} {name:25} {rho_si:6.0f} kg/m^3  ->  {rho_nastran_calc:.3e} kg/mm^3")

        if error >= 0.01:
            all_passed = False
            print(f"      ERROR: {error*100:.2f}% deviation from expected {rho_nastran_expected:.3e}")

        # Round-trip test
        rho_si_roundtrip = density_nastran_to_si(rho_nastran_calc)
        roundtrip_error = abs(rho_si_roundtrip - rho_si) / rho_si

        if roundtrip_error >= 1e-6:
            all_passed = False
            print(f"      ROUND-TRIP ERROR: {roundtrip_error*100:.6f}%")

    # Velocity tests
    print("\n2. Velocity Conversions (m/s -> mm/s)")
    print("-" * 70)

    velocity_tests = [
        ("Low subsonic (100 m/s)", 100, 100000),
        ("Transonic (M=1.0 at SL)", 340, 340000),
        ("Supersonic (M=2.0 at SL)", 680, 680000),
        ("Hypersonic (M=5.0 at SL)", 1700, 1700000),
    ]

    for name, v_si, v_nastran_expected in velocity_tests:
        v_nastran_calc = velocity_si_to_nastran(v_si)
        error = abs(v_nastran_calc - v_nastran_expected) / v_nastran_expected

        status = "[PASS]" if error < 0.01 else "[FAIL]"
        print(f"{status} {name:25} {v_si:6.0f} m/s   ->  {v_nastran_calc:.0f} mm/s")

        if error >= 0.01:
            all_passed = False

    # Stress/modulus tests
    print("\n3. Stress/Modulus Conversions (Pa -> MPa)")
    print("-" * 70)

    stress_tests = [
        ("Aluminum E", 71.7e9, 71700),
        ("Steel E", 200e9, 200000),
        ("Titanium E", 113.8e9, 113800),
    ]

    for name, e_si, e_nastran_expected in stress_tests:
        e_nastran_calc = stress_si_to_nastran(e_si)
        error = abs(e_nastran_calc - e_nastran_expected) / e_nastran_expected

        status = "[PASS]" if error < 0.01 else "[FAIL]"
        print(f"{status} {name:25} {e_si/1e9:6.1f} GPa  ->  {e_nastran_calc:.0f} MPa")

        if error >= 0.01:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] ALL UNIT CONVERSION TESTS PASSED")
        return True
    else:
        print("[FAILURE] SOME UNIT CONVERSION TESTS FAILED")
        return False


def print_conversion_table():
    """Print reference table for NASTRAN unit conversions"""
    print("\nNASTRAN mm-kg-s-N Unit Conversion Reference")
    print("=" * 70)
    print("\nBase Units:")
    print("  Length:          millimeters (mm)")
    print("  Mass:            kilograms (kg)")
    print("  Time:            seconds (s)")
    print("  Force:           Newtons (N)")
    print("\nDerived Units:")
    print("  Stress/Modulus:  N/mm^2 = MPa")
    print("  Density:         kg/mm^3")
    print("  Velocity:        mm/s")
    print("  Acceleration:    mm/s^2")
    print("  Frequency:       Hz = 1/s")
    print("\nCommon Material Properties:")
    print("  Aluminum 6061:   E = 71700 MPa,    rho = 2.81e-9 kg/mm^3")
    print("  Steel 4130:      E = 200000 MPa,   rho = 7.85e-9 kg/mm^3")
    print("  Titanium Ti-6Al-4V: E = 113800 MPa, rho = 4.43e-9 kg/mm^3")
    print("\nCommon Flow Conditions (sea level):")
    print("  Air density:     rho = 1.225e-9 kg/mm^3")
    print("  Speed of sound:  a = 340000 mm/s = 340 m/s")
    print("  Mach 0.8:        V = 272000 mm/s = 272 m/s")
    print("  Mach 2.0:        V = 680000 mm/s = 680 m/s")
    print("=" * 70)


if __name__ == "__main__":
    print_conversion_table()
    print()
    success = validate_conversions()

    import sys
    sys.exit(0 if success else 1)
