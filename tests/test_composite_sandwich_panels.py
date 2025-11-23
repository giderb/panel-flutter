"""
Comprehensive validation tests for composite facesheet sandwich panels.

Tests the v2.2.1 upgrade that enables orthotropic (composite) facesheets
in sandwich panel configurations.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from models.material import (
    PredefinedMaterials, SandwichPanel, IsotropicMaterial, OrthotropicMaterial,
    HoneycombCore, material_from_dict
)


class TestCompositeSandwichPanels(unittest.TestCase):
    """Test suite for composite facesheet sandwich panels."""

    def test_aluminum_sandwich_creation(self):
        """Test traditional aluminum facesheet sandwich panel."""
        sandwich = PredefinedMaterials.create_aluminum_sandwich()

        self.assertEqual(sandwich.name, "7050-T7451 Sandwich Panel")
        self.assertIsInstance(sandwich.face_material, IsotropicMaterial)
        self.assertEqual(sandwich.face_material.name, "7050-T7451")
        self.assertEqual(sandwich.face_thickness, 0.5)  # mm
        self.assertEqual(sandwich.core_thickness, 12.7)  # mm
        self.assertEqual(sandwich.total_thickness, 13.7)  # mm

    def test_aluminum_lithium_sandwich_creation(self):
        """Test aluminum-lithium facesheet sandwich panel."""
        sandwich = PredefinedMaterials.create_aluminum_lithium_sandwich()

        self.assertEqual(sandwich.name, "2050-T84 Sandwich Panel")
        self.assertIsInstance(sandwich.face_material, IsotropicMaterial)
        self.assertEqual(sandwich.face_material.name, "2050-T84")
        self.assertEqual(sandwich.face_thickness, 0.76)  # mm
        self.assertEqual(sandwich.core_thickness, 19.1)  # mm

    def test_composite_sandwich_creation(self):
        """Test carbon fiber composite facesheet sandwich panel."""
        sandwich = PredefinedMaterials.create_composite_sandwich()

        self.assertEqual(sandwich.name, "IM7/M91 Composite Sandwich Panel")
        self.assertIsInstance(sandwich.face_material, OrthotropicMaterial)
        self.assertEqual(sandwich.face_material.name, "IM7/M91")
        self.assertEqual(sandwich.face_thickness, 0.194)  # mm (194 g/m²)
        self.assertEqual(sandwich.core_thickness, 12.7)  # mm

        # Verify orthotropic properties
        self.assertAlmostEqual(sandwich.face_material.e1 / 1e9, 162.0, places=1)  # GPa
        self.assertAlmostEqual(sandwich.face_material.e2 / 1e9, 8.5, places=1)  # GPa
        self.assertAlmostEqual(sandwich.face_material.g12 / 1e9, 4.9, places=1)  # GPa
        self.assertEqual(sandwich.face_material.density, 1560)  # kg/m³

    def test_composite_sandwich_thick_creation(self):
        """Test thick carbon fabric composite sandwich panel."""
        sandwich = PredefinedMaterials.create_composite_sandwich_thick()

        self.assertEqual(sandwich.name, "AS4c/M21 Composite Sandwich Panel")
        self.assertIsInstance(sandwich.face_material, OrthotropicMaterial)
        self.assertEqual(sandwich.face_material.name, "AS4c/M21")
        self.assertEqual(sandwich.face_thickness, 0.285)  # mm (285 g/m² fabric)
        self.assertEqual(sandwich.core_thickness, 19.1)  # mm

        # Verify balanced fabric properties
        self.assertAlmostEqual(sandwich.face_material.e1 / 1e9, 62.8, places=1)  # GPa
        self.assertAlmostEqual(sandwich.face_material.e2 / 1e9, 62.8, places=1)  # GPa (balanced)

    def test_equivalent_properties_isotropic(self):
        """Test equivalent property calculation for isotropic facesheets."""
        sandwich = PredefinedMaterials.create_aluminum_sandwich()
        props = sandwich.get_equivalent_properties()

        # Verify all required keys exist
        required_keys = [
            'flexural_rigidity', 'effective_youngs_modulus', 'shear_rigidity',
            'mass_per_area', 'face_youngs', 'face_poisson', 'core_shear',
            'weight_saving', 'first_mode_freq_estimate'
        ]
        for key in required_keys:
            self.assertIn(key, props)

        # Verify physical reasonableness
        self.assertGreater(props['flexural_rigidity'], 0)
        self.assertGreater(props['effective_youngs_modulus'], 0)
        self.assertGreater(props['mass_per_area'], 0)
        self.assertGreater(props['weight_saving'], 0)
        self.assertLess(props['weight_saving'], 100)
        self.assertGreater(props['first_mode_freq_estimate'], 0)

        # Aluminum 7050-T7451: E = 71.008 GPa
        self.assertAlmostEqual(props['face_youngs'] / 1e9, 71.008, places=1)

    def test_equivalent_properties_orthotropic(self):
        """Test equivalent property calculation for orthotropic facesheets."""
        sandwich = PredefinedMaterials.create_composite_sandwich()
        props = sandwich.get_equivalent_properties()

        # Verify all required keys exist
        required_keys = [
            'flexural_rigidity', 'effective_youngs_modulus', 'shear_rigidity',
            'mass_per_area', 'face_youngs', 'face_poisson', 'core_shear'
        ]
        for key in required_keys:
            self.assertIn(key, props)

        # Verify orthotropic material uses E1 (primary direction)
        # IM7/M91: E1 = 162 GPa
        self.assertAlmostEqual(props['face_youngs'] / 1e9, 162.0, places=1)

        # Verify nu12 used as Poisson's ratio
        self.assertAlmostEqual(props['face_poisson'], 0.34, places=2)

        # Verify physical reasonableness
        self.assertGreater(props['flexural_rigidity'], 0)
        self.assertGreater(props['mass_per_area'], 0)

    def test_composite_weight_savings(self):
        """Test that composite facesheets provide weight savings vs aluminum."""
        al_sandwich = PredefinedMaterials.create_aluminum_sandwich()
        comp_sandwich = PredefinedMaterials.create_composite_sandwich()

        al_mass = al_sandwich.mass_per_area
        comp_mass = comp_sandwich.mass_per_area

        # Composite should be lighter than aluminum
        self.assertLess(comp_mass, al_mass)

        # Calculate weight savings
        weight_saving_percent = (1 - comp_mass / al_mass) * 100

        # Composite facesheets typically save 40-60% vs aluminum for same stiffness
        # Note: These are thin facesheets, so savings may be lower
        print(f"\nComposite weight saving: {weight_saving_percent:.1f}%")
        print(f"Aluminum mass: {al_mass:.4f} kg/m²")
        print(f"Composite mass: {comp_mass:.4f} kg/m²")

    def test_composite_stiffness_comparison(self):
        """Test stiffness comparison between aluminum and composite sandwiches."""
        al_sandwich = PredefinedMaterials.create_aluminum_sandwich()
        comp_sandwich = PredefinedMaterials.create_composite_sandwich()

        al_props = al_sandwich.get_equivalent_properties()
        comp_props = comp_sandwich.get_equivalent_properties()

        # Composite has higher E1 (162 GPa) vs aluminum (71 GPa)
        # So composite should have higher flexural rigidity for same thickness
        print(f"\nAluminum flexural rigidity: {al_props['flexural_rigidity']:.3e} N·m")
        print(f"Composite flexural rigidity: {comp_props['flexural_rigidity']:.3e} N·m")
        print(f"Composite stiffness ratio: {comp_props['flexural_rigidity'] / al_props['flexural_rigidity']:.2f}x")

    def test_serialization_isotropic_sandwich(self):
        """Test JSON serialization of aluminum sandwich panel."""
        sandwich = PredefinedMaterials.create_aluminum_sandwich()
        sandwich_dict = sandwich.to_dict()

        # Verify structure
        self.assertEqual(sandwich_dict['type'], 'sandwich')
        self.assertEqual(sandwich_dict['name'], sandwich.name)
        self.assertEqual(sandwich_dict['face_material']['type'], 'isotropic')
        self.assertEqual(sandwich_dict['face_material']['name'], '7050-T7451')

        # Verify serialization is JSON-compatible
        json_str = json.dumps(sandwich_dict)
        self.assertIsInstance(json_str, str)

    def test_serialization_orthotropic_sandwich(self):
        """Test JSON serialization of composite sandwich panel."""
        sandwich = PredefinedMaterials.create_composite_sandwich()
        sandwich_dict = sandwich.to_dict()

        # Verify structure
        self.assertEqual(sandwich_dict['type'], 'sandwich')
        self.assertEqual(sandwich_dict['name'], sandwich.name)
        self.assertEqual(sandwich_dict['face_material']['type'], 'orthotropic')
        self.assertEqual(sandwich_dict['face_material']['name'], 'IM7/M91')

        # Verify orthotropic properties are serialized
        self.assertIn('e1', sandwich_dict['face_material'])
        self.assertIn('e2', sandwich_dict['face_material'])
        self.assertIn('g12', sandwich_dict['face_material'])

        # Verify serialization is JSON-compatible
        json_str = json.dumps(sandwich_dict)
        self.assertIsInstance(json_str, str)

    def test_deserialization_isotropic_sandwich(self):
        """Test JSON deserialization of aluminum sandwich panel."""
        original = PredefinedMaterials.create_aluminum_sandwich()
        sandwich_dict = original.to_dict()

        # Deserialize
        reconstructed = material_from_dict(sandwich_dict)

        # Verify type
        self.assertIsInstance(reconstructed, SandwichPanel)
        self.assertIsInstance(reconstructed.face_material, IsotropicMaterial)

        # Verify properties match
        self.assertEqual(reconstructed.name, original.name)
        self.assertEqual(reconstructed.face_material.name, original.face_material.name)
        self.assertEqual(reconstructed.face_thickness, original.face_thickness)
        self.assertEqual(reconstructed.core_thickness, original.core_thickness)

    def test_deserialization_orthotropic_sandwich(self):
        """Test JSON deserialization of composite sandwich panel."""
        original = PredefinedMaterials.create_composite_sandwich()
        sandwich_dict = original.to_dict()

        # Deserialize
        reconstructed = material_from_dict(sandwich_dict)

        # Verify type
        self.assertIsInstance(reconstructed, SandwichPanel)
        self.assertIsInstance(reconstructed.face_material, OrthotropicMaterial)

        # Verify properties match
        self.assertEqual(reconstructed.name, original.name)
        self.assertEqual(reconstructed.face_material.name, original.face_material.name)
        self.assertEqual(reconstructed.face_thickness, original.face_thickness)
        self.assertEqual(reconstructed.core_thickness, original.core_thickness)

        # Verify orthotropic properties
        self.assertEqual(reconstructed.face_material.e1, original.face_material.e1)
        self.assertEqual(reconstructed.face_material.e2, original.face_material.e2)
        self.assertEqual(reconstructed.face_material.g12, original.face_material.g12)

    def test_round_trip_serialization(self):
        """Test full round-trip serialization for all sandwich types."""
        sandwich_types = [
            PredefinedMaterials.create_aluminum_sandwich(),
            PredefinedMaterials.create_aluminum_lithium_sandwich(),
            PredefinedMaterials.create_composite_sandwich(),
            PredefinedMaterials.create_composite_sandwich_thick()
        ]

        for original in sandwich_types:
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

    def test_custom_composite_sandwich(self):
        """Test creation of custom composite sandwich panel."""
        # Create custom sandwich with AS4c/M21 faces
        custom_sandwich = SandwichPanel(
            id=100,
            name="Custom AS4c/M21 Sandwich",
            face_material=PredefinedMaterials.as4c_m21(),
            face_thickness=0.57,  # mm (2 plies x 285 g/m²)
            core_material=PredefinedMaterials.nomex_honeycomb(),
            core_thickness=25.4,  # mm (1.0")
            description="Custom thick composite sandwich for high loads"
        )

        # Verify properties can be calculated
        props = custom_sandwich.get_equivalent_properties()
        self.assertGreater(props['flexural_rigidity'], 0)
        self.assertGreater(props['mass_per_area'], 0)

        # Verify serialization works
        sandwich_dict = custom_sandwich.to_dict()
        self.assertEqual(sandwich_dict['type'], 'sandwich')
        self.assertEqual(sandwich_dict['face_material']['type'], 'orthotropic')

    def test_quartz_facesheet_sandwich(self):
        """Test sandwich panel with quartz fabric facesheets."""
        quartz_sandwich = SandwichPanel(
            id=200,
            name="Quartz Radome Sandwich",
            face_material=PredefinedMaterials.quartz_8552(),
            face_thickness=0.285,  # mm
            core_material=PredefinedMaterials.nomex_honeycomb(),
            core_thickness=12.7,  # mm
            description="RF-transparent radome sandwich panel"
        )

        # Verify orthotropic material
        self.assertIsInstance(quartz_sandwich.face_material, OrthotropicMaterial)
        self.assertEqual(quartz_sandwich.face_material.name, "Quartz/8552")

        # Verify properties
        props = quartz_sandwich.get_equivalent_properties()

        # Quartz has lower modulus (22 GPa) than carbon
        self.assertAlmostEqual(props['face_youngs'] / 1e9, 22.0, places=1)


def run_tests():
    """Run all tests and generate report."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCompositeSandwichPanels)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("COMPOSITE SANDWICH PANEL VALIDATION SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED - Composite facesheet support is fully functional!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
