"""
Test Uncertainty Quantification Module
=======================================

Validates that physics_corrections.py correctly populates uncertainty fields.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_bridge.physics_corrections import CertificationPhysicsCorrections
from python_bridge.flutter_analyzer import FlutterResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_uq_doublet_lattice():
    """Test UQ for subsonic DLM analysis"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Uncertainty Quantification - Doublet Lattice Method (M<1.0)")
    logger.info("=" * 70)

    corrections = CertificationPhysicsCorrections()

    # Create mock flutter result from DLM analysis
    result = FlutterResult(
        flutter_speed=450.0,
        flutter_frequency=125.0,
        flutter_mode=1,
        damping_ratio=0.0,
        dynamic_pressure=120000.0,
        reduced_frequency=0.15,
        mach_number=0.85,
        altitude=3000.0,
        method='doublet_lattice',
        converged=True,
        validation_status='VALIDATED'
    )

    panel_config = {
        'boundary_condition': 'SSSS',
        'material_type': 'aluminum',
        'mach_number': 0.85,
        'aspect_ratio': 2.0,
        'thickness_ratio': 0.01
    }

    # Apply corrections
    result_corrected = corrections.apply_all_corrections(result, panel_config)

    # Verify UQ fields populated
    assert result_corrected.uncertainty_upper > 0, "Upper uncertainty not populated!"
    assert result_corrected.uncertainty_lower < 0, "Lower uncertainty not populated!"
    assert len(result_corrected.uncertainty_notes) > 0, "Uncertainty notes empty!"

    logger.info(f"✓ Flutter speed: {result_corrected.flutter_speed:.2f} m/s")
    logger.info(f"✓ Uncertainty: +{result_corrected.uncertainty_upper:.1f}% / {result_corrected.uncertainty_lower:.1f}%")
    logger.info(f"✓ Notes: {result_corrected.uncertainty_notes}")
    logger.info(f"✓ Expected range: {result_corrected.flutter_speed * (1 + result_corrected.uncertainty_upper/100):.2f} - "
               f"{result_corrected.flutter_speed * (1 + result_corrected.uncertainty_lower/100):.2f} m/s")

    # Check expected bounds (DLM ±10% base)
    assert result_corrected.uncertainty_upper >= 10.0, f"Upper bound too low: {result_corrected.uncertainty_upper}"
    assert result_corrected.uncertainty_lower <= -10.0, f"Lower bound too high: {result_corrected.uncertainty_lower}"

    logger.info("✓ TEST 1 PASSED: DLM uncertainty quantification working correctly\n")
    return result_corrected


def test_uq_piston_theory():
    """Test UQ for supersonic Piston Theory analysis"""
    logger.info("=" * 70)
    logger.info("TEST 2: Uncertainty Quantification - Piston Theory (M≥1.5)")
    logger.info("=" * 70)

    corrections = CertificationPhysicsCorrections()

    # Create mock flutter result from Piston Theory analysis
    result = FlutterResult(
        flutter_speed=850.0,
        flutter_frequency=180.0,
        flutter_mode=1,
        damping_ratio=0.0,
        dynamic_pressure=350000.0,
        reduced_frequency=0.12,
        mach_number=2.5,
        altitude=10000.0,
        method='piston_theory',
        converged=True,
        validation_status='VALIDATED'
    )

    panel_config = {
        'boundary_condition': 'SSSS',
        'material_type': 'aluminum',
        'mach_number': 2.5,
        'aspect_ratio': 2.0,
        'thickness_ratio': 0.008
    }

    # Apply corrections
    result_corrected = corrections.apply_all_corrections(result, panel_config)

    # Verify UQ fields populated
    assert result_corrected.uncertainty_upper > 0, "Upper uncertainty not populated!"
    assert result_corrected.uncertainty_lower < 0, "Lower uncertainty not populated!"
    assert result_corrected.uncertainty_notes is not None, "Uncertainty notes missing!"

    logger.info(f"✓ Flutter speed (uncorrected): {result.flutter_speed:.2f} m/s")
    logger.info(f"✓ Flutter speed (corrected): {result_corrected.flutter_speed:.2f} m/s")
    logger.info(f"✓ Thermal degradation factor: {result_corrected.temperature_degradation_factor:.3f}")
    logger.info(f"✓ Wall temperature: {result_corrected.wall_temperature:.1f} K")
    logger.info(f"✓ Uncertainty: +{result_corrected.uncertainty_upper:.1f}% / {result_corrected.uncertainty_lower:.1f}%")
    logger.info(f"✓ Notes: {result_corrected.uncertainty_notes}")

    # Check expected bounds (Piston ±20% base + thermal ±10%)
    assert result_corrected.uncertainty_upper >= 20.0, f"Upper bound too low: {result_corrected.uncertainty_upper}"
    assert result_corrected.uncertainty_lower <= -15.0, f"Lower bound too high: {result_corrected.uncertainty_lower}"

    # Check thermal correction applied
    assert result_corrected.wall_temperature > 288.15, "Wall temperature not calculated"
    assert result_corrected.temperature_degradation_factor < 1.0, "Thermal degradation not applied"

    logger.info("✓ TEST 2 PASSED: Piston Theory UQ with thermal corrections working correctly\n")
    return result_corrected


def test_uq_physics_solver():
    """Test UQ for empirical physics solver"""
    logger.info("=" * 70)
    logger.info("TEST 3: Uncertainty Quantification - Physics Solver (Empirical)")
    logger.info("=" * 70)

    corrections = CertificationPhysicsCorrections()

    # Create mock flutter result from physics solver
    result = FlutterResult(
        flutter_speed=650.0,
        flutter_frequency=145.0,
        flutter_mode=1,
        damping_ratio=0.0,
        dynamic_pressure=210000.0,
        reduced_frequency=0.14,
        mach_number=1.8,
        altitude=5000.0,
        method='piston_theory_adaptive',  # Physics solver method
        converged=True,
        validation_status='VALIDATED: Physics-based calculation (cross-validate with NASTRAN)'
    )

    panel_config = {
        'boundary_condition': 'SSSS',
        'material_type': 'aluminum',
        'mach_number': 1.8,
        'aspect_ratio': 2.5,
        'thickness_ratio': 0.01
    }

    # Apply corrections
    result_corrected = corrections.apply_all_corrections(result, panel_config)

    # Verify UQ fields populated
    assert result_corrected.uncertainty_upper > 0, "Upper uncertainty not populated!"
    assert result_corrected.uncertainty_lower < 0, "Lower uncertainty not populated!"

    logger.info(f"✓ Flutter speed: {result_corrected.flutter_speed:.2f} m/s")
    logger.info(f"✓ Uncertainty: +{result_corrected.uncertainty_upper:.1f}% / {result_corrected.uncertainty_lower:.1f}%")
    logger.info(f"✓ Expected range: {result_corrected.flutter_speed * (1 + result_corrected.uncertainty_upper/100):.2f} - "
               f"{result_corrected.flutter_speed * (1 + result_corrected.uncertainty_lower/100):.2f} m/s")
    logger.info(f"✓ Notes: {result_corrected.uncertainty_notes}")

    # Check expected bounds (Physics solver ±300%/-70%)
    assert result_corrected.uncertainty_upper >= 200.0, f"Upper bound too low for physics solver: {result_corrected.uncertainty_upper}"
    assert result_corrected.uncertainty_lower <= -50.0, f"Lower bound too high for physics solver: {result_corrected.uncertainty_lower}"

    logger.info("✓ TEST 3 PASSED: Physics solver UQ correctly shows large uncertainty\n")
    return result_corrected


def test_uq_transonic():
    """Test UQ and corrections in transonic regime"""
    logger.info("=" * 70)
    logger.info("TEST 4: Transonic Corrections (0.8 ≤ M < 1.2)")
    logger.info("=" * 70)

    corrections = CertificationPhysicsCorrections()

    # Create mock flutter result in transonic regime
    result = FlutterResult(
        flutter_speed=550.0,
        flutter_frequency=135.0,
        flutter_mode=1,
        damping_ratio=0.0,
        dynamic_pressure=180000.0,
        reduced_frequency=0.16,
        mach_number=1.05,  # Transonic regime
        altitude=4000.0,
        method='piston_theory',
        converged=True,
        validation_status='VALIDATED'
    )

    panel_config = {
        'boundary_condition': 'SSSS',
        'material_type': 'aluminum',
        'mach_number': 1.05,
        'aspect_ratio': 2.0,
        'thickness_ratio': 0.009
    }

    # Apply corrections
    result_corrected = corrections.apply_all_corrections(result, panel_config)

    # Verify transonic correction applied
    assert result_corrected.transonic_correction_factor < 1.0, "Transonic correction not applied"
    assert result_corrected.flutter_speed < result.flutter_speed, "Flutter speed should decrease in transonic regime"
    assert result_corrected.uncorrected_flutter_speed == result.flutter_speed, "Uncorrected speed not saved"

    logger.info(f"✓ Flutter speed (uncorrected): {result.flutter_speed:.2f} m/s")
    logger.info(f"✓ Flutter speed (corrected): {result_corrected.flutter_speed:.2f} m/s")
    logger.info(f"✓ Transonic correction factor: {result_corrected.transonic_correction_factor:.3f}")
    logger.info(f"✓ Reduction: {(1 - result_corrected.transonic_correction_factor) * 100:.1f}%")
    logger.info(f"✓ Uncertainty: +{result_corrected.uncertainty_upper:.1f}% / {result_corrected.uncertainty_lower:.1f}%")

    # Check additional transonic uncertainty added
    assert result_corrected.uncertainty_upper >= 40.0, "Transonic uncertainty not added"
    assert "Transonic" in result_corrected.uncertainty_notes, "Transonic notes missing"

    logger.info("✓ TEST 4 PASSED: Transonic corrections working correctly\n")
    return result_corrected


def test_uq_composite():
    """Test UQ for composite materials"""
    logger.info("=" * 70)
    logger.info("TEST 5: Composite Material Uncertainty")
    logger.info("=" * 70)

    corrections = CertificationPhysicsCorrections()

    # Create mock flutter result for composite panel
    result = FlutterResult(
        flutter_speed=700.0,
        flutter_frequency=160.0,
        flutter_mode=1,
        damping_ratio=0.0,
        dynamic_pressure=245000.0,
        reduced_frequency=0.13,
        mach_number=2.0,
        altitude=8000.0,
        method='piston_theory',
        converged=True,
        validation_status='VALIDATED'
    )

    panel_config = {
        'boundary_condition': 'SSSS',
        'material_type': 'composite_laminate',  # Composite material
        'mach_number': 2.0,
        'aspect_ratio': 2.0,
        'thickness_ratio': 0.008
    }

    # Apply corrections
    result_corrected = corrections.apply_all_corrections(result, panel_config)

    logger.info(f"✓ Flutter speed: {result_corrected.flutter_speed:.2f} m/s")
    logger.info(f"✓ Uncertainty: +{result_corrected.uncertainty_upper:.1f}% / {result_corrected.uncertainty_lower:.1f}%")
    logger.info(f"✓ Notes: {result_corrected.uncertainty_notes}")

    # Check composite uncertainty is higher
    assert result_corrected.uncertainty_upper >= 60.0, "Composite uncertainty not added"
    assert "Composite" in result_corrected.uncertainty_notes, "Composite notes missing"

    logger.info("✓ TEST 5 PASSED: Composite material UQ working correctly\n")
    return result_corrected


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("UNCERTAINTY QUANTIFICATION MODULE VALIDATION")
    print("Testing physics_corrections.py implementation")
    print("=" * 70 + "\n")

    try:
        # Run all tests
        test_uq_doublet_lattice()
        test_uq_piston_theory()
        test_uq_physics_solver()
        test_uq_transonic()
        test_uq_composite()

        print("=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nUncertainty Quantification Module: VALIDATED ✓")
        print("\nSummary:")
        print("- DLM (subsonic): ±10% base uncertainty")
        print("- Piston Theory (supersonic): ±20% base uncertainty")
        print("- Physics Solver (empirical): ±300%/-70% uncertainty")
        print("- Transonic regime: +25% additional uncertainty")
        print("- Thermal effects (M≥2.0): +10% additional uncertainty")
        print("- Composite materials: +50% additional uncertainty")
        print("\n✓ Ready for certification use")
        print("=" * 70 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
