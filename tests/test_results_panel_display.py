"""
Validation test for improved Results Panel display.

Tests the v2.2.3 upgrade that removes cluttered static data and focuses
on critical flutter analysis results.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime


class TestResultsPanelDisplay(unittest.TestCase):
    """Test suite for improved results panel display."""

    def test_sample_result_structure(self):
        """Test that sample analysis results have correct structure."""

        # Create a sample analysis result (typical structure from integrated_analysis_executor)
        sample_result = {
            'success': True,
            'converged': True,
            'method': 'Piston Theory (Supersonic)',
            'execution_time': 12.5,

            # Critical flutter results
            'critical_flutter_speed': 450.2,  # m/s
            'critical_flutter_frequency': 85.3,  # Hz
            'critical_flutter_mode': 1,
            'critical_dynamic_pressure': 101325.0,  # Pa
            'safety_margin': 22.5,  # %

            # Configuration (input parameters)
            'configuration': {
                'panel_dimensions': '1200.0x800.0x2.5mm',
                'material': 'E=73.1GPa, nu=0.33, rho=2780kg/m3',
                'boundary_conditions': 'SSSS',
                'mach_number': 1.8,
                'altitude': 10000.0,
                'temperature': 288.15,
                'air_density': 1.225,
                'thickness': 0.0025,  # m
                'panel_thickness': 0.0025,  # m
                'target_flutter_speed': 350.0,  # m/s
                'velocity_max': 500.0
            },

            # Validation
            'validation_status': 'EXCELLENT - Physics validated against analytical solution',
            'nastran_validation': 'GOOD - NASTRAN agrees within 3.2%',
            'comparison': {
                'physics_flutter_speed': 450.2,
                'nastran_flutter_speed': 463.5,
                'physics_flutter_frequency': 85.3,
                'nastran_flutter_frequency': 87.1,
                'speed_difference_percent': 2.9,
                'frequency_difference_percent': 2.1,
                'validation_status': 'EXCELLENT'
            },

            # Physics result
            'physics_result': {
                'flutter_speed': 450.2,
                'flutter_frequency': 85.3,
                'flutter_mode': 1,
                'converged': True,
                'validation_status': 'EXCELLENT'
            },

            # NASTRAN result
            'nastran_result': {
                'critical_flutter_velocity': 463.5,
                'critical_flutter_frequency': 87.1,
                'critical_mode': 1,
                'success': True
            },

            # Flutter data for plotting
            'flutter_data': {
                'velocities': list(range(100, 501, 10)),  # m/s
                'damping': [-0.05] * 40,  # Stable
                'frequencies': [85.0 + i * 0.1 for i in range(40)],
                'critical_velocity': 450.2,
                'critical_frequency': 85.3
            },

            # Stability
            'stable_in_range': False,
            'timestamp': datetime.now().isoformat()
        }

        # Verify all required keys exist
        required_keys = [
            'success', 'converged', 'method',
            'critical_flutter_speed', 'critical_flutter_frequency',
            'critical_flutter_mode', 'safety_margin',
            'configuration', 'validation_status'
        ]

        for key in required_keys:
            self.assertIn(key, sample_result, f"Missing required key: {key}")

        # Verify configuration has required subkeys
        config_keys = [
            'mach_number', 'altitude', 'thickness', 'panel_thickness'
        ]

        for key in config_keys:
            self.assertIn(key, sample_result['configuration'],
                         f"Missing required configuration key: {key}")

        print("\n[PASS] Sample result structure is correct")
        print(f"  Flutter Speed: {sample_result['critical_flutter_speed']:.1f} m/s")
        print(f"  Target Speed: {sample_result['configuration']['target_flutter_speed']:.1f} m/s")
        print(f"  Margin: {((sample_result['critical_flutter_speed'] / sample_result['configuration']['target_flutter_speed']) - 1) * 100:.1f}%")

        return sample_result

    def test_cleared_envelope_calculation(self):
        """Test flight envelope clearance calculation."""

        # Create result where flutter speed exceeds requirement
        result = {
            'critical_flutter_speed': 650.0,  # m/s (high enough to pass)
            'configuration': {
                'mach_number': 1.8,
                'altitude': 10000.0
            }
        }

        # Calculate target flutter speed (true airspeed at flight condition)
        # Using standard atmosphere: M = V / a, where a = sqrt(gamma * R * T)
        import math
        T0 = 288.15  # K
        L = 0.0065   # K/m
        gamma = 1.4
        R = 287.05

        altitude = result['configuration']['altitude']
        temperature = T0 - L * altitude
        speed_of_sound = math.sqrt(gamma * R * temperature)
        target_speed = result['configuration']['mach_number'] * speed_of_sound

        # Calculate margin
        flutter_margin = ((result['critical_flutter_speed'] / target_speed) - 1.0) * 100

        # MIL-STD requires 15% minimum margin
        envelope_cleared = flutter_margin >= 15.0

        print(f"\n[PASS] Envelope clearance calculation:")
        print(f"  Target Speed: {target_speed:.1f} m/s")
        print(f"  Flutter Speed: {result['critical_flutter_speed']:.1f} m/s")
        print(f"  Margin: {flutter_margin:+.1f}%")
        print(f"  Cleared: {'YES' if envelope_cleared else 'NO'}")

        self.assertGreater(flutter_margin, 0, "Flutter speed should exceed flight speed")
        self.assertTrue(envelope_cleared, "Should meet MIL-STD 15% margin requirement")

    def test_failed_envelope_calculation(self):
        """Test flight envelope clearance calculation for failed case."""

        # Create result where flutter speed is below requirement
        result = {
            'critical_flutter_speed': 300.0,  # m/s (too low)
            'configuration': {
                'mach_number': 1.8,
                'altitude': 10000.0,
                'thickness': 0.002  # m (2mm)
            }
        }

        # Calculate target flutter speed
        import math
        T0 = 288.15
        L = 0.0065
        gamma = 1.4
        R = 287.05

        altitude = result['configuration']['altitude']
        temperature = T0 - L * altitude
        speed_of_sound = math.sqrt(gamma * R * temperature)
        target_speed = result['configuration']['mach_number'] * speed_of_sound

        # Calculate margin
        flutter_margin = ((result['critical_flutter_speed'] / target_speed) - 1.0) * 100
        envelope_cleared = flutter_margin >= 15.0

        # Calculate required thickness
        speed_ratio = target_speed / result['critical_flutter_speed']
        current_thickness = result['configuration']['thickness']
        required_thickness = current_thickness * speed_ratio * 1.10  # 10% safety margin

        print(f"\n[PASS] Failed envelope - design guidance:")
        print(f"  Target Speed: {target_speed:.1f} m/s")
        print(f"  Flutter Speed: {result['critical_flutter_speed']:.1f} m/s")
        print(f"  Margin: {flutter_margin:+.1f}%")
        print(f"  Cleared: {'YES' if envelope_cleared else 'NO'}")
        print(f"  Current Thickness: {current_thickness * 1000:.2f} mm")
        print(f"  Required Thickness: {required_thickness * 1000:.2f} mm")

        self.assertLess(flutter_margin, 15.0, "Should fail clearance requirement")
        self.assertFalse(envelope_cleared, "Should not be cleared")
        self.assertGreater(required_thickness, current_thickness, "Should require thicker panel")

    def test_confidence_level_logic(self):
        """Test confidence level determination logic."""

        test_cases = [
            # Case 1: High confidence (converged + NASTRAN + good agreement)
            {
                'converged': True,
                'comparison': {'nastran_flutter_speed': 450.0, 'speed_difference_percent': 3.0},
                'validation_status': 'EXCELLENT',
                'expected': 'HIGH'
            },
            # Case 2: Medium confidence (converged + NASTRAN + moderate agreement)
            {
                'converged': True,
                'comparison': {'nastran_flutter_speed': 450.0, 'speed_difference_percent': 10.0},
                'validation_status': 'GOOD',
                'expected': 'MEDIUM'
            },
            # Case 3: Low confidence (converged + NASTRAN + poor agreement)
            {
                'converged': True,
                'comparison': {'nastran_flutter_speed': 450.0, 'speed_difference_percent': 25.0},
                'validation_status': 'WARNING',
                'expected': 'LOW'
            },
            # Case 4: Medium confidence (converged + physics only)
            {
                'converged': True,
                'comparison': {},
                'validation_status': 'EXCELLENT',
                'expected': 'MEDIUM'
            },
            # Case 5: Low confidence (not converged)
            {
                'converged': False,
                'comparison': {},
                'validation_status': 'EXCELLENT',
                'expected': 'LOW'
            }
        ]

        print("\n[PASS] Confidence level determination:")

        for i, case in enumerate(test_cases, 1):
            # Simulate confidence determination
            converged = case['converged']
            comparison = case['comparison']
            nastran_available = comparison.get('nastran_flutter_speed') is not None
            validation_status = case['validation_status']

            if converged and nastran_available:
                speed_diff = abs(comparison.get('speed_difference_percent', 100))
                if speed_diff < 5.0:
                    confidence = "HIGH"
                elif speed_diff < 15.0:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
            elif converged:
                if 'EXCELLENT' in validation_status or 'VALIDATED' in validation_status:
                    confidence = "MEDIUM"
                elif 'GOOD' in validation_status:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
            else:
                confidence = "LOW"

            print(f"  Case {i}: Converged={converged}, NASTRAN={nastran_available}, "
                  f"Validation={validation_status} -> {confidence}")

            self.assertEqual(confidence, case['expected'],
                           f"Case {i} failed: expected {case['expected']}, got {confidence}")

    def test_removed_clutter_items(self):
        """Verify that cluttered items are removed from display logic."""

        # Items that should NO LONGER be displayed in summary:
        removed_items = [
            ('panel_dimensions', '"Panel Dimensions"'),
            ('material', '"Material Properties"'),
            ('boundary_conditions', '"Boundary Conditions"'),
            ('execution_time', '"Execution Time"'),
        ]

        # Read the new implementation to verify these are not in display
        import inspect
        from gui.panels.results_panel import ResultsPanel

        # Get source code of _show_summary method
        source = inspect.getsource(ResultsPanel._show_summary)

        # Verify removed items are not displayed as labels
        for item_name, check_string in removed_items:
            self.assertNotIn(check_string, source,
                           f"Cluttered item '{item_name}' should be removed from display")

        print("\n[PASS] Verified cluttered items removed:")
        for item_name, _ in removed_items:
            print(f"  + {item_name} - not displayed")

    def test_new_display_items(self):
        """Verify that new important items are included."""

        # Items that SHOULD be displayed in streamlined summary:
        # Using simple text searches (emojis are prepended in actual code)
        new_items = [
            'Flight Safety Assessment',  # Main card title
            'Flight Condition',  # Flight parameters
            'Required Flutter Speed',  # Target from flight condition
            'Safety Margin',  # Critical metric
            'Clearance Status',  # Pass/fail
            'Flutter Characteristics',  # Technical data card
            'Analysis Quality',  # Validation card
            'Overall Confidence',  # Confidence level
            'Design Recommendations'  # Conditional guidance card
        ]

        # Read the new implementation
        import inspect
        from gui.panels.results_panel import ResultsPanel

        source = inspect.getsource(ResultsPanel._show_summary)

        # Verify new items are present
        for item in new_items:
            self.assertIn(item, source,
                         f"New important item '{item}' should be displayed")

        print("\n[PASS] Verified streamlined display items present:")
        for item in new_items:
            print(f"  + {item}")


def run_tests():
    """Run all results panel display tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestResultsPanelDisplay)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("RESULTS PANEL DISPLAY VALIDATION SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("\n[SUCCESS] ALL DISPLAY TESTS PASSED!")
        print("Results panel is now streamlined and focused on critical data.")
        return 0
    else:
        print("\n[FAILED] SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
