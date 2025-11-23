"""
Comprehensive validation tests for composite laminate facesheet sandwich panels.

Tests the v2.2.2 upgrade that enables CompositeLaminate facesheets
in sandwich panel configurations.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from models.material import (
    PredefinedMaterials, SandwichPanel, IsotropicMaterial, OrthotropicMaterial,
    CompositeLaminate, CompositeLamina, HoneycombCore, material_from_dict
)


class TestLaminateSandwichPanels(unittest.TestCase):
    """Test suite for composite laminate facesheet sandwich panels."""

    def test_laminate_sandwich_creation(self):
        """Test sandwich panel with composite laminate facesheets."""
        sandwich = PredefinedMaterials.create_laminate_sandwich()

        self.assertEqual(sandwich.name, "Laminate Facesheet Sandwich Panel")
        self.assertIsInstance(sandwich.face_material, CompositeLaminate)
        self.assertEqual(sandwich.face_material.name, "IM7/M91 [0/90]s Laminate")
        self.assertEqual(len(sandwich.face_material.laminas), 4)
        self.assertEqual(sandwich.face_thickness, 0.50)  # mm
        self.assertEqual(sandwich.core_thickness, 12.7)  # mm

        # Verify laminate structure
        self.assertEqual(sandwich.face_material.laminas[0].orientation, 0)   # 0°
        self.assertEqual(sandwich.face_material.laminas[1].orientation, 90)  # 90°
        self.assertEqual(sandwich.face_material.laminas[2].orientation, 90)  # 90°
        self.assertEqual(sandwich.face_material.laminas[3].orientation, 0)   # 0°

    def test_laminate_total_thickness(self):
        """Test that laminate total thickness is calculated correctly."""
        sandwich = PredefinedMaterials.create_laminate_sandwich()

        laminate_thickness = sandwich.face_material.total_thickness
        self.assertAlmostEqual(laminate_thickness, 0.50, places=2)  # 4 × 0.125 mm

    def test_equivalent_properties_laminate(self):
        """Test equivalent property calculation for laminate facesheets."""
        sandwich = PredefinedMaterials.create_laminate_sandwich()
        props = sandwich.get_equivalent_properties()

        # Verify all required keys exist
        required_keys = [
            'flexural_rigidity', 'effective_youngs_modulus', 'shear_rigidity',
            'mass_per_area', 'face_youngs', 'face_poisson', 'core_shear'
        ]
        for key in required_keys:
            self.assertIn(key, props)

        # Verify smeared properties are calculated
        # [0/90]s laminate should have E between E1 and E2
        # E1 = 162 GPa, E2 = 8.5 GPa
        # Smeared E = (2×162 + 2×8.5) / 4 = 85.25 GPa (simplification, actual weighted)
        face_E = props['face_youngs'] / 1e9  # Convert to GPa
        self.assertGreater(face_E, 8.5)    # Greater than E2
        self.assertLess(face_E, 162.0)      # Less than E1

        print(f"\n[0/90]s Laminate smeared E: {face_E:.1f} GPa")
        print(f"  Expected range: 8.5 - 162 GPa")
        print(f"  Weighted average (50/50): ~85.25 GPa")

        # Verify physical reasonableness
        self.assertGreater(props['flexural_rigidity'], 0)
        self.assertGreater(props['mass_per_area'], 0)

    def test_laminate_density_calculation(self):
        """Test smeared density calculation for laminate facesheets."""
        sandwich = PredefinedMaterials.create_laminate_sandwich()

        # All laminas use IM7/M91 with density = 1560 kg/m³
        # So smeared density should be 1560 kg/m³
        face_density = sandwich._get_face_density()
        self.assertAlmostEqual(face_density, 1560, places=0)

        # Verify mass per area calculation
        props = sandwich.get_equivalent_properties()
        self.assertGreater(props['mass_per_area'], 0)

    def test_mixed_material_laminate(self):
        """Test laminate with different materials in different plies."""
        carbon = PredefinedMaterials.im7_m91()     # E1 = 162 GPa, ρ = 1560 kg/m³
        fabric = PredefinedMaterials.as4c_m21()    # E1 = 62.8 GPa, ρ = 1580 kg/m³

        laminas = [
            CompositeLamina(1, carbon, 0.194, 0),     # High-modulus outer ply
            CompositeLamina(2, fabric, 0.285, 45),    # Fabric for impact resistance
            CompositeLamina(3, fabric, 0.285, -45),   # Fabric for impact resistance
            CompositeLamina(4, carbon, 0.194, 0),     # High-modulus outer ply
        ]

        laminate = CompositeLaminate(
            id=20,
            name="Hybrid IM7/AS4c Laminate",
            laminas=laminas,
            description="Hybrid carbon/fabric for stiffness + toughness"
        )

        sandwich = SandwichPanel(
            id=100,
            name="Hybrid Facesheet Sandwich",
            face_material=laminate,
            face_thickness=0.958,  # mm (2×0.194 + 2×0.285)
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7
        )

        # Calculate properties
        props = sandwich.get_equivalent_properties()

        # Smeared E should be between carbon (162) and fabric (62.8)
        face_E = props['face_youngs'] / 1e9
        self.assertGreater(face_E, 62.8)
        self.assertLess(face_E, 162.0)

        # Smeared density should be between 1560 and 1580
        face_density = sandwich._get_face_density()
        self.assertGreater(face_density, 1560)
        self.assertLess(face_density, 1580)

        print(f"\nHybrid Laminate smeared E: {face_E:.1f} GPa")
        print(f"Hybrid Laminate smeared density: {face_density:.0f} kg/m^3")

    def test_serialization_laminate_sandwich(self):
        """Test JSON serialization of laminate sandwich panel."""
        sandwich = PredefinedMaterials.create_laminate_sandwich()
        sandwich_dict = sandwich.to_dict()

        # Verify structure
        self.assertEqual(sandwich_dict['type'], 'sandwich')
        self.assertEqual(sandwich_dict['name'], sandwich.name)
        self.assertEqual(sandwich_dict['face_material']['type'], 'composite')
        self.assertEqual(sandwich_dict['face_material']['name'], 'IM7/M91 [0/90]s Laminate')

        # Verify laminate structure is serialized
        self.assertIn('laminas', sandwich_dict['face_material'])
        self.assertEqual(len(sandwich_dict['face_material']['laminas']), 4)

        # Verify lamina details
        first_lamina = sandwich_dict['face_material']['laminas'][0]
        self.assertIn('material', first_lamina)
        self.assertIn('thickness', first_lamina)
        self.assertIn('orientation', first_lamina)
        self.assertEqual(first_lamina['orientation'], 0)

        # Verify serialization is JSON-compatible
        json_str = json.dumps(sandwich_dict)
        self.assertIsInstance(json_str, str)

    def test_deserialization_laminate_sandwich(self):
        """Test JSON deserialization of laminate sandwich panel."""
        original = PredefinedMaterials.create_laminate_sandwich()
        sandwich_dict = original.to_dict()

        # Deserialize
        reconstructed = material_from_dict(sandwich_dict)

        # Verify type
        self.assertIsInstance(reconstructed, SandwichPanel)
        self.assertIsInstance(reconstructed.face_material, CompositeLaminate)

        # Verify properties match
        self.assertEqual(reconstructed.name, original.name)
        self.assertEqual(reconstructed.face_material.name, original.face_material.name)
        self.assertEqual(len(reconstructed.face_material.laminas), len(original.face_material.laminas))
        self.assertEqual(reconstructed.face_thickness, original.face_thickness)
        self.assertEqual(reconstructed.core_thickness, original.core_thickness)

        # Verify lamina details match
        for i in range(len(original.face_material.laminas)):
            orig_lamina = original.face_material.laminas[i]
            recon_lamina = reconstructed.face_material.laminas[i]
            self.assertEqual(recon_lamina.thickness, orig_lamina.thickness)
            self.assertEqual(recon_lamina.orientation, orig_lamina.orientation)
            self.assertEqual(recon_lamina.material.name, orig_lamina.material.name)

    def test_round_trip_serialization_laminate(self):
        """Test full round-trip serialization for laminate sandwich."""
        original = PredefinedMaterials.create_laminate_sandwich()

        # Serialize to dict
        sandwich_dict = original.to_dict()

        # Convert to JSON string and back
        json_str = json.dumps(sandwich_dict)
        reconstructed_dict = json.loads(json_str)

        # Deserialize back to object
        reconstructed = material_from_dict(reconstructed_dict)

        # Verify
        self.assertEqual(reconstructed.name, original.name)
        self.assertEqual(reconstructed.face_thickness, original.face_thickness)
        self.assertEqual(reconstructed.core_thickness, original.core_thickness)
        self.assertEqual(type(reconstructed.face_material), type(original.face_material))
        self.assertEqual(len(reconstructed.face_material.laminas), len(original.face_material.laminas))

        # Verify equivalent properties are the same
        orig_props = original.get_equivalent_properties()
        recon_props = reconstructed.get_equivalent_properties()

        self.assertAlmostEqual(orig_props['flexural_rigidity'], recon_props['flexural_rigidity'], places=3)
        self.assertAlmostEqual(orig_props['mass_per_area'], recon_props['mass_per_area'], places=6)

    def test_comparison_laminate_vs_single_ply(self):
        """Compare laminate facesheet vs single orthotropic ply."""
        # Laminate sandwich
        laminate_sandwich = PredefinedMaterials.create_laminate_sandwich()
        laminate_props = laminate_sandwich.get_equivalent_properties()

        # Single ply sandwich with same total thickness
        single_ply_sandwich = SandwichPanel(
            id=200,
            name="Single Ply Comparison",
            face_material=PredefinedMaterials.im7_m91(),
            face_thickness=0.50,  # Same as laminate total
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7
        )
        single_ply_props = single_ply_sandwich.get_equivalent_properties()

        # Laminate has smeared E (average of 0° and 90°)
        # Single ply has full E1 (0° only)
        # So single ply should have higher stiffness
        self.assertGreater(single_ply_props['face_youngs'], laminate_props['face_youngs'])

        print(f"\nLaminate [0/90]s E: {laminate_props['face_youngs']/1e9:.1f} GPa")
        print(f"Single 0° ply E: {single_ply_props['face_youngs']/1e9:.1f} GPa")
        print(f"Ratio: {single_ply_props['face_youngs'] / laminate_props['face_youngs']:.2f}x")

        # But mass should be the same (same material, same thickness)
        self.assertAlmostEqual(laminate_props['mass_per_area'],
                             single_ply_props['mass_per_area'],
                             places=4)

    def test_quasi_isotropic_laminate(self):
        """Test quasi-isotropic laminate [0/45/-45/90]s."""
        carbon = PredefinedMaterials.im7_m91()

        laminas = [
            CompositeLamina(1, carbon, 0.125, 0),      # 0°
            CompositeLamina(2, carbon, 0.125, 45),     # 45°
            CompositeLamina(3, carbon, 0.125, -45),    # -45°
            CompositeLamina(4, carbon, 0.125, 90),     # 90°
            CompositeLamina(5, carbon, 0.125, 90),     # 90° (mirror)
            CompositeLamina(6, carbon, 0.125, -45),    # -45°
            CompositeLamina(7, carbon, 0.125, 45),     # 45°
            CompositeLamina(8, carbon, 0.125, 0),      # 0°
        ]

        laminate = CompositeLaminate(
            id=30,
            name="IM7/M91 [0/45/-45/90]s",
            laminas=laminas,
            description="Quasi-isotropic laminate"
        )

        sandwich = SandwichPanel(
            id=300,
            name="Quasi-Isotropic Sandwich",
            face_material=laminate,
            face_thickness=1.0,  # mm (8 × 0.125)
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7
        )

        props = sandwich.get_equivalent_properties()

        # Quasi-isotropic should have more balanced properties
        # Smeared E should be ~(E1 + E2)/2 but weighted by ply orientations
        # [0/45/-45/90]s has equal plies in each direction
        face_E = props['face_youngs'] / 1e9
        print(f"\nQuasi-isotropic [0/45/-45/90]s E: {face_E:.1f} GPa")

        # Should be somewhere between E1 and E2
        self.assertGreater(face_E, 8.5)    # E2
        self.assertLess(face_E, 162.0)      # E1

    def test_zero_thickness_laminate_error(self):
        """Test that zero-thickness laminate raises error."""
        carbon = PredefinedMaterials.im7_m91()

        # Create laminate with zero thickness plies
        laminas = [
            CompositeLamina(1, carbon, 0.0, 0),
            CompositeLamina(2, carbon, 0.0, 90),
        ]

        laminate = CompositeLaminate(
            id=40,
            name="Zero Thickness Test",
            laminas=laminas
        )

        sandwich = SandwichPanel(
            id=400,
            name="Zero Thickness Sandwich",
            face_material=laminate,
            face_thickness=0.0,
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7
        )

        # Should raise ValueError when calculating properties
        with self.assertRaises(ValueError):
            sandwich.get_equivalent_properties()


def run_tests():
    """Run all tests and generate report."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLaminateSandwichPanels)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("LAMINATE FACESHEET SANDWICH PANEL VALIDATION SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("\n[SUCCESS] ALL TESTS PASSED - Laminate facesheet support is fully functional!")
        return 0
    else:
        print("\n[FAILED] SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
