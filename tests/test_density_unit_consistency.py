"""
Density Unit Consistency Validation Tests
==========================================

Critical safety test to verify all density conversions use consistent
NASTRAN unit system (mm-tonne-s-N).

SAFETY CRITICAL: Inconsistent density units cause sqrt(1000)x = 31.6x
error in flutter speed predictions.

Run with:
    .\.venv\Scripts\python.exe tests\test_density_unit_consistency.py
"""

import sys
from pathlib import Path
import unittest
import tempfile
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from python_bridge.simple_bdf_generator import SimpleBDFGenerator
from python_bridge.unit_conversions import (
    density_si_to_nastran, density_nastran_to_si,
    density_si_to_nastran_tonne, density_nastran_tonne_to_si
)
from python_bridge.bdf_generator_sol145_fixed import create_sol145_flutter_bdf

# Try to import composite material classes for MAT8 testing
try:
    from models.material import OrthotropicMaterial, CompositeLaminate, CompositeLamina
    COMPOSITE_AVAILABLE = True
except ImportError:
    COMPOSITE_AVAILABLE = False


class TestDensityUnitConsistency(unittest.TestCase):
    """Test that all density values use consistent unit system"""

    def test_mat1_density_is_tonne_mm3(self):
        """Verify MAT1 RHO field is in tonne/mm3 (not kg/mm3)

        Aluminum: 2810 kg/m3 converted to tonne/mm3:
        - 1 kg = 0.001 tonne
        - 1 m3 = 10^9 mm3
        - Factor: 10^-3 / 10^9 = 10^-12
        - Result: 2810 * 10^-12 = 2.81e-9 tonne/mm3

        If the value is ~2.81e-6, the code is using kg/mm3 (WRONG - 1000x error)
        If the value is ~2.81e-9, the code is using tonne/mm3 (CORRECT)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SimpleBDFGenerator(output_dir=tmpdir)
            bdf_path = generator.generate_flutter_bdf(
                length=1.0,
                width=0.5,
                thickness=0.003,
                nx=5,
                ny=5,
                youngs_modulus=71.7e9,
                poissons_ratio=0.33,
                density=2810,  # kg/m3
                mach_number=2.0,
                velocities=[500, 600, 700],
                output_file="test_mat1.bdf"
            )

            with open(bdf_path, 'r') as f:
                content = f.read()

            # Extract MAT1 card RHO field
            # MAT1 format: MAT1 MID E G NU RHO A ...
            # Looking for scientific notation like 2.81E-12 or 2.81-12
            mat1_match = re.search(
                r'MAT1\s+\d+\s+[\d.E+-]+\s+[\d.E+-]+\s+[\d.]+\s+([\d.E+-]+)',
                content
            )
            self.assertIsNotNone(mat1_match, "MAT1 card not found in BDF")

            rho_str = mat1_match.group(1).strip()
            # Handle NASTRAN compact notation (e.g., 2.81-12 instead of 2.81E-12)
            if 'E' not in rho_str.upper() and '-' in rho_str[1:]:
                # Find the exponent position (not the leading sign)
                for i in range(1, len(rho_str)):
                    if rho_str[i] == '-' or rho_str[i] == '+':
                        rho_str = rho_str[:i] + 'E' + rho_str[i:]
                        break

            rho_value = float(rho_str)

            # Expected: 2.81e-9 tonne/mm3 (tolerance: 1%)
            # Math: 2810 kg/m3 * 1e-12 = 2810 * 10^-12 = 2.81 * 10^-9 tonne/mm3
            # (1 tonne = 1000 kg, 1 m3 = 10^9 mm3, so factor = 10^-3 / 10^9 = 10^-12)
            expected_rho = 2.81e-9
            self.assertAlmostEqual(
                rho_value, expected_rho, delta=expected_rho * 0.01,
                msg=f"MAT1 RHO should be ~{expected_rho:.2e} tonne/mm3, got {rho_value:.2e}. "
                    f"If ~2.81e-6, density may be in kg/mm3 (1000x error!)"
            )

    def test_aero_density_is_tonne_mm3(self):
        """Verify AERO card RHOREF is in tonne/mm3

        Sea level air: 1.225 kg/m3 converted to tonne/mm3:
        - Factor: 10^-12 (same as material)
        - Result: 1.225 * 10^-12 = 1.225e-12 tonne/mm3

        If ~1e-9, using kg/mm3 (WRONG - 1000x error with material density)
        If ~1e-12, using tonne/mm3 (CORRECT)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SimpleBDFGenerator(output_dir=tmpdir)
            bdf_path = generator.generate_flutter_bdf(
                length=1.0,
                width=0.5,
                thickness=0.003,
                nx=5,
                ny=5,
                youngs_modulus=71.7e9,
                poissons_ratio=0.33,
                density=2810,
                mach_number=2.0,
                velocities=[500, 600, 700],
                output_file="test_aero.bdf"
            )

            with open(bdf_path, 'r') as f:
                content = f.read()

            # Extract AERO card RHOREF field
            # AERO format: AERO ACSID VELOCITY REFC RHOREF
            aero_match = re.search(
                r'AERO\s+\d+\s+[\d.]+\s+[\d.]+\s+([\d.E+-]+)',
                content
            )
            self.assertIsNotNone(aero_match, "AERO card not found in BDF")

            rho_str = aero_match.group(1).strip()
            # Handle NASTRAN compact notation
            if 'E' not in rho_str.upper() and ('-' in rho_str[1:] or '+' in rho_str[1:]):
                for i in range(1, len(rho_str)):
                    if rho_str[i] == '-' or rho_str[i] == '+':
                        rho_str = rho_str[:i] + 'E' + rho_str[i:]
                        break

            rho_value = float(rho_str)

            # Should be order of 1e-12 tonne/mm3, not 1e-9 kg/mm3
            self.assertLess(
                rho_value, 1e-10,
                msg=f"AERO RHOREF should be ~1e-12 tonne/mm3, got {rho_value:.2e}. "
                    f"Value > 1e-10 suggests kg/mm3 (wrong unit system!)"
            )
            self.assertGreater(
                rho_value, 1e-14,
                msg=f"AERO RHOREF too small: {rho_value:.2e}"
            )

    def test_density_ratio_is_correct(self):
        """Verify material/air density ratio is physically reasonable

        Aluminum/Air ratio should be ~2294 (2810/1.225)

        If ratio is ~2.29, material is in tonne/mm3 but air is in kg/mm3 (1000x error)
        If ratio is ~2,294,000, air is in tonne/mm3 but material is in kg/mm3 (1000x error)
        If ratio is ~2294, both use same unit system (CORRECT)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SimpleBDFGenerator(output_dir=tmpdir)
            bdf_path = generator.generate_flutter_bdf(
                length=1.0,
                width=0.5,
                thickness=0.003,
                nx=5,
                ny=5,
                youngs_modulus=71.7e9,
                poissons_ratio=0.33,
                density=2810,  # Aluminum
                mach_number=2.0,
                velocities=[500, 600, 700],
                output_file="test_ratio.bdf"
            )

            with open(bdf_path, 'r') as f:
                content = f.read()

            # Extract MAT1 density
            mat1_match = re.search(
                r'MAT1\s+\d+\s+[\d.E+-]+\s+[\d.E+-]+\s+[\d.]+\s+([\d.E+-]+)',
                content
            )
            # Extract AERO density
            aero_match = re.search(
                r'AERO\s+\d+\s+[\d.]+\s+[\d.]+\s+([\d.E+-]+)',
                content
            )

            self.assertIsNotNone(mat1_match, "MAT1 card not found")
            self.assertIsNotNone(aero_match, "AERO card not found")

            # Parse density values (handle NASTRAN compact notation)
            def parse_nastran_float(s):
                s = s.strip()
                if 'E' not in s.upper() and ('-' in s[1:] or '+' in s[1:]):
                    for i in range(1, len(s)):
                        if s[i] == '-' or s[i] == '+':
                            s = s[:i] + 'E' + s[i:]
                            break
                return float(s)

            rho_material = parse_nastran_float(mat1_match.group(1))
            rho_air = parse_nastran_float(aero_match.group(1))

            ratio = rho_material / rho_air
            expected_ratio = 2810 / 1.225  # ~2294

            # Allow 50% tolerance for altitude effects on air density
            self.assertGreater(
                ratio, expected_ratio * 0.5,
                msg=f"Density ratio too low ({ratio:.1f}). Expected ~{expected_ratio:.0f}. "
                    f"Ratio < 100 suggests material in tonne/mm3 but air in kg/mm3!"
            )
            self.assertLess(
                ratio, expected_ratio * 2.0,
                msg=f"Density ratio too high ({ratio:.1f}). Expected ~{expected_ratio:.0f}. "
                    f"Ratio > 10000 suggests air in tonne/mm3 but material in kg/mm3!"
            )

    def test_round_trip_conversion(self):
        """Verify round-trip conversion accuracy in unit_conversions module"""
        test_densities = [2810, 7850, 1600, 4430]  # Al, Steel, CFRP, Ti (kg/m3)

        for rho_si in test_densities:
            rho_nastran = density_si_to_nastran(rho_si)
            rho_si_back = density_nastran_to_si(rho_nastran)

            self.assertAlmostEqual(
                rho_si, rho_si_back, delta=1e-6,
                msg=f"Round-trip failed for {rho_si} kg/m3: "
                    f"got {rho_si_back} after round-trip"
            )

    def test_tonne_conversion_round_trip(self):
        """Verify round-trip tonne/mm3 conversion accuracy"""
        test_densities = [2810, 7850, 1600, 4430, 1.225]  # materials + air

        for rho_si in test_densities:
            rho_tonne = density_si_to_nastran_tonne(rho_si)
            rho_si_back = density_nastran_tonne_to_si(rho_tonne)

            self.assertAlmostEqual(
                rho_si, rho_si_back, delta=rho_si * 1e-10,
                msg=f"Tonne round-trip failed for {rho_si} kg/m3"
            )

    def test_tonne_conversion_values(self):
        """Verify tonne/mm3 conversion produces correct values"""
        # Aluminum: 2810 kg/m3 * 1e-12 = 2.81e-9 tonne/mm3
        rho_al = density_si_to_nastran_tonne(2810)
        self.assertAlmostEqual(rho_al, 2.81e-9, delta=1e-12,
            msg=f"Aluminum tonne conversion wrong: {rho_al}")

        # Air at sea level: 1.225 kg/m3 * 1e-12 = 1.225e-12 tonne/mm3
        rho_air = density_si_to_nastran_tonne(1.225)
        self.assertAlmostEqual(rho_air, 1.225e-12, delta=1e-15,
            msg=f"Air tonne conversion wrong: {rho_air}")

    @unittest.skipUnless(COMPOSITE_AVAILABLE, "Composite material classes not available")
    def test_mat8_composite_density_is_tonne_mm3(self):
        """Verify MAT8 RHO field uses tonne/mm3 (not kg/mm3)

        CRITICAL FLIGHT SAFETY TEST: This test validates that composite
        material density in MAT8 cards uses the same 1e-12 factor as
        isotropic materials in MAT1 cards.

        CFRP: 1600 kg/m3 * 1e-12 = 1.6e-9 tonne/mm3 (CORRECT)
        If the value is ~1.6e-6, the code is using 1e-9 (kg/mm3) - WRONG!
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple composite laminate
            cfrp = OrthotropicMaterial(
                id=1,
                name="T300/5208_CFRP",
                e1=181e9,    # Pa
                e2=10.3e9,   # Pa
                g12=7.17e9,  # Pa
                nu12=0.28,
                density=1600  # kg/m3
            )

            # Create a [0/90/90/0] laminate
            laminate = CompositeLaminate(
                id=1,
                name="Test_Laminate",
                laminas=[
                    CompositeLamina(id=1, material=cfrp, thickness=0.125, orientation=0),
                    CompositeLamina(id=2, material=cfrp, thickness=0.125, orientation=90),
                    CompositeLamina(id=3, material=cfrp, thickness=0.125, orientation=90),
                    CompositeLamina(id=4, material=cfrp, thickness=0.125, orientation=0),
                ]
            )

            generator = SimpleBDFGenerator(output_dir=tmpdir)
            bdf_path = generator.generate_flutter_bdf(
                length=0.5,
                width=0.3,
                thickness=0.0005,  # Will be overridden by laminate
                nx=5,
                ny=5,
                youngs_modulus=181e9,  # Dummy, overridden
                poissons_ratio=0.28,
                density=1600,  # Dummy, overridden
                mach_number=2.0,
                velocities=[500, 600, 700],
                output_file="test_mat8.bdf",
                material_object=laminate  # Pass composite material
            )

            with open(bdf_path, 'r') as f:
                content = f.read()

            # Extract MAT8 card RHO field
            # MAT8 format: MAT8 MID E1 E2 NU12 G12 G1Z G2Z RHO
            # Note: NASTRAN format uses compact field notation (no spaces between fields)
            mat8_match = re.search(
                r'MAT8\s+(\d+)\s*([\d.E+-]+)([\d.E+-]+)\s*([\d.E+-]+)\s*([\d.E+-]+)\s*([\d.E+-]+)\s*([\d.E+-]+)\s*([\d.E+-]+)',
                content
            )

            self.assertIsNotNone(mat8_match,
                "MAT8 card not found in BDF. Composite generation may have failed.")

            # RHO is in the 8th field (group 8)
            rho_str = mat8_match.group(8).strip()
            # Handle NASTRAN compact notation
            if 'E' not in rho_str.upper() and ('-' in rho_str[1:] or '+' in rho_str[1:]):
                for i in range(1, len(rho_str)):
                    if rho_str[i] == '-' or rho_str[i] == '+':
                        rho_str = rho_str[:i] + 'E' + rho_str[i:]
                        break

            rho_value = float(rho_str)

            # Expected: 1.6e-9 tonne/mm3 (tolerance: 1%)
            # CFRP: 1600 kg/m3 * 1e-12 = 1.6e-9 tonne/mm3
            expected_rho = 1.6e-9

            # CRITICAL: If value is ~1.6e-6, the bug was NOT fixed
            if rho_value > 1e-7:
                self.fail(
                    f"CRITICAL SAFETY FAILURE: MAT8 RHO = {rho_value:.2e} suggests "
                    f"kg/mm3 units (1e-9 factor) instead of tonne/mm3 (1e-12 factor). "
                    f"This is a 1000x error that causes ~31.6x flutter speed error!"
                )

            self.assertAlmostEqual(
                rho_value, expected_rho, delta=expected_rho * 0.05,
                msg=f"MAT8 RHO should be ~{expected_rho:.2e} tonne/mm3, got {rho_value:.2e}"
            )

    def test_unit_conversion_factor(self):
        """Verify the unit conversion uses correct 1e-9 factor for kg/mm3

        This module uses mm-kg-s-N system (1e-9 factor).
        BDF generators use mm-tonne-s-N system (1e-12 factor).
        """
        # Test the documented behavior: SI to NASTRAN (kg/mm3)
        rho_si = 2810  # kg/m3
        rho_nastran = density_si_to_nastran(rho_si)

        # unit_conversions.py uses kg/mm3 system (1e-9 factor)
        expected = 2810 * 1e-9  # 2.81e-6 kg/mm3

        self.assertAlmostEqual(
            rho_nastran, expected, delta=1e-15,
            msg=f"density_si_to_nastran should use 1e-9 factor (kg/mm3). "
                f"Got {rho_nastran}, expected {expected}"
        )

    def test_create_sol145_flutter_bdf_density_consistency(self):
        """Test that create_sol145_flutter_bdf uses consistent density units

        This tests the standalone function which has a separate code path.
        Material and air density must both use the same unit system.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config for create_sol145_flutter_bdf
            config = {
                'panel_length': 1000.0,  # mm
                'panel_width': 500.0,    # mm
                'thickness': 3.0,        # mm
                'nx': 5,
                'ny': 5,
                'youngs_modulus': 71700.0,  # MPa
                'poissons_ratio': 0.33,
                'density': 2.81e-9,  # tonne/mm3 (already converted!)
                'mach_number': 2.0,
                'altitude': 0,  # Sea level for known air density
                'velocities': [500000, 600000, 700000],  # mm/s
                'output_filename': 'test_create_sol145.bdf'
            }

            bdf_path = create_sol145_flutter_bdf(config, output_dir=tmpdir)

            with open(bdf_path, 'r') as f:
                content = f.read()

            # Extract MAT1 density
            mat1_match = re.search(
                r'MAT1\s+\d+\s+[\d.E+-]+\s+[\d.E+-]+\s+[\d.]+\s+([\d.E+-]+)',
                content
            )
            # Extract AERO density
            aero_match = re.search(
                r'AERO\s+\d+\s+[\d.]+\s+[\d.]+\s+([\d.E+-]+)',
                content
            )

            self.assertIsNotNone(mat1_match, "MAT1 card not found")
            self.assertIsNotNone(aero_match, "AERO card not found")

            # Parse density values
            def parse_nastran_float(s):
                s = s.strip()
                if 'E' not in s.upper() and ('-' in s[1:] or '+' in s[1:]):
                    for i in range(1, len(s)):
                        if s[i] == '-' or s[i] == '+':
                            s = s[:i] + 'E' + s[i:]
                            break
                return float(s)

            rho_material = parse_nastran_float(mat1_match.group(1))
            rho_air = parse_nastran_float(aero_match.group(1))

            # Check that both are in the same order of magnitude (both 1e-9 or both 1e-12)
            # If one is 1e-9 and the other is 1e-12, ratio would be ~1000x off
            ratio = rho_material / rho_air
            expected_ratio = 2810 / 1.225  # ~2294

            # Allow 50% tolerance for altitude effects
            self.assertGreater(
                ratio, expected_ratio * 0.5,
                msg=f"Density ratio too low ({ratio:.1f}). Expected ~{expected_ratio:.0f}. "
                    f"This indicates MAT1 and AERO use different unit systems!"
            )
            self.assertLess(
                ratio, expected_ratio * 2.0,
                msg=f"Density ratio too high ({ratio:.1f}). Expected ~{expected_ratio:.0f}. "
                    f"This indicates MAT1 and AERO use different unit systems!"
            )


class TestFlutterSpeedSanityCheck(unittest.TestCase):
    """Sanity checks for flutter speed predictions"""

    def test_aluminum_panel_flutter_speed_reasonable(self):
        """
        Verify flutter speed is physically reasonable for typical aluminum panel.

        A 1m x 0.5m x 6mm aluminum panel at M=2.0 should flutter around 500-1500 m/s.
        If flutter speed is < 50 m/s or > 5000 m/s, something is likely wrong with units.

        Impact of density errors:
        - If density is 1000x too high: flutter speed ~31.6x too low
        - If density is 1000x too low: flutter speed ~31.6x too high
        """
        try:
            from python_bridge.flutter_analyzer import PanelFlutterAnalyzer, PanelProperties, FlowConditions
        except ImportError:
            self.skipTest("flutter_analyzer not available")

        # Create panel and flow conditions
        panel = PanelProperties(
            length=1.0,
            width=0.5,
            thickness=0.006,
            youngs_modulus=71.7e9,
            poissons_ratio=0.33,
            density=2810,
            boundary_conditions="SSSS"
        )

        flow = FlowConditions(
            mach_number=2.0,
            altitude=10000,
            density=0.4135  # kg/m3 at 10km altitude
        )

        # Run physics-based flutter analysis
        analyzer = PanelFlutterAnalyzer()
        result = analyzer.analyze_flutter(
            panel, flow,
            velocity_range=(100, 2000),
            n_points=20
        )

        # Check flutter speed is reasonable
        if result.converged and result.flutter_speed < 9000:
            self.assertGreater(
                result.flutter_speed, 50,
                msg=f"Flutter speed too low ({result.flutter_speed:.0f} m/s). "
                    f"Check if density conversion has 1000x error!"
            )
            self.assertLess(
                result.flutter_speed, 5000,
                msg=f"Flutter speed too high ({result.flutter_speed:.0f} m/s). "
                    f"Check if density conversion has 1000x error!"
            )


def run_tests():
    """Run all density unit consistency tests"""
    print("\n" + "=" * 70)
    print("DENSITY UNIT CONSISTENCY VALIDATION")
    print("=" * 70)
    print("\nCRITICAL: These tests verify density units are consistent across")
    print("material (MAT1/MAT8) and aerodynamic (AERO) cards.")
    print("Inconsistent units cause ~31.6x error in flutter speed predictions!")
    print("=" * 70 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDensityUnitConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestFlutterSpeedSanityCheck))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("ALL DENSITY UNIT TESTS PASSED")
        print("Material and aerodynamic densities are consistent.")
    else:
        print("DENSITY UNIT TESTS FAILED")
        print("WARNING: Inconsistent units may cause ~31.6x flutter speed error!")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
