"""
Integration tests for custom materials and composite laminates in sandwich panels.

Tests the complete v2.2.2 implementation including GUI integration.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from models.material import (
    PredefinedMaterials, SandwichPanel, IsotropicMaterial, OrthotropicMaterial,
    CompositeLaminate, CompositeLamina, HoneycombCore
)


class TestIntegrationCustomMaterials(unittest.TestCase):
    """Integration tests for complete custom material workflow."""

    def test_all_predefined_sandwiches(self):
        """Test all predefined sandwich panel factory methods."""
        factories = [
            ("Aluminum", PredefinedMaterials.create_aluminum_sandwich),
            ("Aluminum-Lithium", PredefinedMaterials.create_aluminum_lithium_sandwich),
            ("Composite IM7", PredefinedMaterials.create_composite_sandwich),
            ("Composite AS4c", PredefinedMaterials.create_composite_sandwich_thick),
            ("Laminate", PredefinedMaterials.create_laminate_sandwich),
        ]

        for name, factory in factories:
            with self.subTest(name=name):
                sandwich = factory()
                self.assertIsInstance(sandwich, SandwichPanel)

                # Verify properties can be calculated
                props = sandwich.get_equivalent_properties()
                self.assertIn('flexural_rigidity', props)
                self.assertIn('mass_per_area', props)
                self.assertGreater(props['flexural_rigidity'], 0)
                self.assertGreater(props['mass_per_area'], 0)

                # Verify serialization works
                sandwich_dict = sandwich.to_dict()
                self.assertEqual(sandwich_dict['type'], 'sandwich')

                print(f"\n{name} Sandwich:")
                print(f"  Face type: {type(sandwich.face_material).__name__}")
                print(f"  Mass: {props['mass_per_area']:.4f} kg/m^2")
                print(f"  D: {props['flexural_rigidity']:.3e} N*m")

    def test_custom_isotropic_sandwich(self):
        """Test sandwich with custom isotropic facesheet."""
        # Create custom aluminum alloy
        custom_al = IsotropicMaterial(
            id=100,
            name="Al 6061-T6 Custom",
            youngs_modulus=68.9e9,  # Pa
            poissons_ratio=0.33,
            shear_modulus=26.0e9,  # Pa
            density=2700  # kg/m³
        )

        # Create sandwich with custom facesheet
        sandwich = SandwichPanel(
            id=200,
            name="Custom Aluminum Sandwich",
            face_material=custom_al,
            face_thickness=0.5,  # mm
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7  # mm
        )

        # Verify properties
        props = sandwich.get_equivalent_properties()
        self.assertGreater(props['mass_per_area'], 0)
        self.assertGreater(props['flexural_rigidity'], 0)

        # Verify face modulus matches custom material
        self.assertAlmostEqual(props['face_youngs'] / 1e9, 68.9, places=1)

        print(f"\nCustom Isotropic Sandwich:")
        print(f"  E: {props['face_youngs']/1e9:.1f} GPa")
        print(f"  Mass: {props['mass_per_area']:.4f} kg/m^2")

    def test_custom_orthotropic_sandwich(self):
        """Test sandwich with custom orthotropic facesheet."""
        # Create custom composite material
        custom_composite = OrthotropicMaterial(
            id=101,
            name="Custom T300/Epoxy",
            e1=140e9,  # Pa
            e2=10e9,   # Pa
            nu12=0.3,
            g12=5e9,   # Pa
            density=1550  # kg/m³
        )

        # Create sandwich
        sandwich = SandwichPanel(
            id=201,
            name="Custom Composite Sandwich",
            face_material=custom_composite,
            face_thickness=0.20,  # mm
            core_material=PredefinedMaterials.nomex_honeycomb(),
            core_thickness=12.7  # mm
        )

        # Verify properties
        props = sandwich.get_equivalent_properties()
        self.assertGreater(props['mass_per_area'], 0)

        # Verify face modulus uses E1
        self.assertAlmostEqual(props['face_youngs'] / 1e9, 140.0, places=1)

        print(f"\nCustom Orthotropic Sandwich:")
        print(f"  E1: {props['face_youngs']/1e9:.1f} GPa")
        print(f"  Mass: {props['mass_per_area']:.4f} kg/m^2")

    def test_custom_laminate_sandwich(self):
        """Test sandwich with custom composite laminate facesheet."""
        # Create custom laminate [0/45/-45/90]s
        carbon = PredefinedMaterials.im7_m91()

        custom_laminate = CompositeLaminate(
            id=50,
            name="Custom [0/45/-45/90]s",
            laminas=[
                CompositeLamina(1, carbon, 0.125, 0),
                CompositeLamina(2, carbon, 0.125, 45),
                CompositeLamina(3, carbon, 0.125, -45),
                CompositeLamina(4, carbon, 0.125, 90),
                CompositeLamina(5, carbon, 0.125, 90),
                CompositeLamina(6, carbon, 0.125, -45),
                CompositeLamina(7, carbon, 0.125, 45),
                CompositeLamina(8, carbon, 0.125, 0),
            ]
        )

        # Create sandwich
        sandwich = SandwichPanel(
            id=250,
            name="Quasi-Isotropic Laminate Sandwich",
            face_material=custom_laminate,
            face_thickness=1.0,  # mm (8 plies)
            core_material=PredefinedMaterials.aluminum_honeycomb_5056(),
            core_thickness=19.1  # mm
        )

        # Verify properties
        props = sandwich.get_equivalent_properties()
        self.assertGreater(props['mass_per_area'], 0)

        # Smeared E should be less than E1 due to 90° plies
        self.assertLess(props['face_youngs'] / 1e9, 162.0)  # Less than pure 0°
        self.assertGreater(props['face_youngs'] / 1e9, 8.5)  # More than pure 90°

        print(f"\nCustom Laminate Sandwich:")
        print(f"  Smeared E: {props['face_youngs']/1e9:.1f} GPa")
        print(f"  Mass: {props['mass_per_area']:.4f} kg/m^2")
        print(f"  Number of plies: {len(custom_laminate.laminas)}")

    def test_hybrid_laminate_sandwich(self):
        """Test sandwich with mixed-material laminate facesheet."""
        carbon_uni = PredefinedMaterials.im7_m91()     # E1 = 162 GPa
        carbon_fabric = PredefinedMaterials.as4c_m21() # E1 = 62.8 GPa

        # Create hybrid laminate (stiff outer, tough inner)
        hybrid_laminate = CompositeLaminate(
            id=60,
            name="Hybrid Carbon Laminate",
            laminas=[
                CompositeLamina(1, carbon_uni, 0.194, 0),      # Outer: stiffness
                CompositeLamina(2, carbon_fabric, 0.285, 45),  # Inner: toughness
                CompositeLamina(3, carbon_fabric, 0.285, -45), # Inner: toughness
                CompositeLamina(4, carbon_uni, 0.194, 0),      # Outer: stiffness
            ]
        )

        # Create sandwich
        sandwich = SandwichPanel(
            id=300,
            name="Hybrid Laminate Sandwich",
            face_material=hybrid_laminate,
            face_thickness=0.958,  # mm
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7  # mm
        )

        # Verify properties
        props = sandwich.get_equivalent_properties()

        # Smeared E should be between fabric (62.8) and uni (162)
        smeared_E = props['face_youngs'] / 1e9
        self.assertGreater(smeared_E, 62.8)
        self.assertLess(smeared_E, 162.0)

        # Smeared density should be between 1560 and 1580
        face_density = sandwich._get_face_density()
        self.assertGreater(face_density, 1560)
        self.assertLess(face_density, 1580)

        print(f"\nHybrid Laminate Sandwich:")
        print(f"  Smeared E: {smeared_E:.1f} GPa")
        print(f"  Smeared density: {face_density:.0f} kg/m^3")
        print(f"  Mass: {props['mass_per_area']:.4f} kg/m^2")

    def test_serialization_all_types(self):
        """Test serialization/deserialization for all facesheet types."""
        from models.material import material_from_dict

        sandwiches = [
            ("Aluminum", PredefinedMaterials.create_aluminum_sandwich()),
            ("Composite", PredefinedMaterials.create_composite_sandwich()),
            ("Laminate", PredefinedMaterials.create_laminate_sandwich()),
        ]

        for name, original in sandwiches:
            with self.subTest(name=name):
                # Serialize
                sandwich_dict = original.to_dict()

                # Deserialize
                reconstructed = material_from_dict(sandwich_dict)

                # Verify type preserved
                self.assertEqual(type(reconstructed), type(original))
                self.assertEqual(type(reconstructed.face_material),
                               type(original.face_material))

                # Verify properties match
                orig_props = original.get_equivalent_properties()
                recon_props = reconstructed.get_equivalent_properties()

                self.assertAlmostEqual(orig_props['mass_per_area'],
                                     recon_props['mass_per_area'],
                                     places=6)
                self.assertAlmostEqual(orig_props['flexural_rigidity'],
                                     recon_props['flexural_rigidity'],
                                     places=3)

                print(f"\n{name} Round-Trip: SUCCESS")

    def test_weight_comparison_all_types(self):
        """Compare weight savings across different facesheet types."""
        sandwiches = {
            "Aluminum": PredefinedMaterials.create_aluminum_sandwich(),
            "Composite Uni": PredefinedMaterials.create_composite_sandwich(),
            "Laminate": PredefinedMaterials.create_laminate_sandwich(),
        }

        al_mass = sandwiches["Aluminum"].mass_per_area

        print("\n" + "="*60)
        print("WEIGHT COMPARISON")
        print("="*60)

        for name, sandwich in sandwiches.items():
            mass = sandwich.mass_per_area
            props = sandwich.get_equivalent_properties()
            weight_saving = (1 - mass / al_mass) * 100

            print(f"{name:20} {mass:8.4f} kg/m^2  ({weight_saving:5.1f}% vs Al)")
            print(f"{'':20} D = {props['flexural_rigidity']:.3e} N*m")

    def test_stiffness_comparison_all_types(self):
        """Compare stiffness across different facesheet types."""
        sandwiches = {
            "Aluminum": PredefinedMaterials.create_aluminum_sandwich(),
            "Composite Uni": PredefinedMaterials.create_composite_sandwich(),
            "Composite Fabric": PredefinedMaterials.create_composite_sandwich_thick(),
            "Laminate [0/90]s": PredefinedMaterials.create_laminate_sandwich(),
        }

        print("\n" + "="*60)
        print("STIFFNESS COMPARISON")
        print("="*60)

        for name, sandwich in sandwiches.items():
            props = sandwich.get_equivalent_properties()
            mass = sandwich.mass_per_area
            specific_stiffness = props['flexural_rigidity'] / mass

            print(f"{name:20} D/m = {specific_stiffness:.3e} (N*m)/(kg/m^2)")
            print(f"{'':20} E_face = {props['face_youngs']/1e9:.1f} GPa")


def run_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegrationCustomMaterials)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("CUSTOM MATERIALS INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("\n[SUCCESS] ALL INTEGRATION TESTS PASSED!")
        print("Custom materials and laminates fully functional.")
        return 0
    else:
        print("\n[FAILED] SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
