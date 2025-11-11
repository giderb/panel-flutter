"""
Test script for user's exact configuration: 500×400×5mm aluminum panel at M=1.27
Expected flutter speed: ~1077 m/s
"""

import sys
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from python_bridge.flutter_analyzer import FlutterAnalyzer, PanelProperties, FlowConditions

# User's exact configuration from screenshot
panel = PanelProperties(
    length=0.5,  # 500 mm = 0.5 m
    width=0.4,   # 400 mm = 0.4 m
    thickness=0.005,  # 5 mm = 0.005 m
    youngs_modulus=71.7e9,  # Aluminum, Pa
    poissons_ratio=0.33,
    density=2700,  # kg/m³
    boundary_conditions='SSSS',
    structural_damping=0.005
)

flow = FlowConditions(
    mach_number=1.27,
    altitude=0.0  # 0 feet = 0 m
)

# FlowConditions will auto-calculate ISA properties via __post_init__

print("=" * 80)
print("USER CONFIGURATION TEST")
print("=" * 80)
print(f"Panel: {panel.length*1000:.0f}×{panel.width*1000:.0f}×{panel.thickness*1000:.1f} mm")
print(f"Material: Aluminum (E={panel.youngs_modulus/1e9:.1f} GPa, rho={panel.density} kg/m^3)")
print(f"Mach: {flow.mach_number}")
print(f"Altitude: {flow.altitude} ft")
print()

# Create analyzer
analyzer = FlutterAnalyzer()

# Test 1: Analytical calculation (should give ~1077 m/s)
print("TEST 1: Analytical Flutter Speed (Dowell's method)")
print("-" * 80)
analytical_speed = analyzer._calculate_dowell_flutter_speed(panel, flow)
print(f"Analytical flutter speed: {analytical_speed:.1f} m/s")
print()

# Test 2: Piston theory analysis with proper velocity range
print("TEST 2: Piston Theory Analysis")
print("-" * 80)
velocity_range = (100, 2000)  # Wide range to capture flutter
result = analyzer._piston_theory_analysis(panel, flow, velocity_range=velocity_range, velocity_points=30)

print(f"Flutter speed: {result.flutter_speed:.1f} m/s")
print(f"Flutter frequency: {result.flutter_frequency:.1f} Hz")
print(f"Flutter mode: {result.flutter_mode}")
print(f"Converged: {result.converged}")
print(f"Validation: {result.validation_status}")
print()

# Test 3: Check if it's close to expected
print("TEST 3: Validation")
print("-" * 80)
expected = 1077.0
actual = result.flutter_speed
error_percent = abs(actual - expected) / expected * 100

print(f"Expected: {expected:.1f} m/s")
print(f"Actual: {actual:.1f} m/s")
print(f"Error: {error_percent:.1f}%")

if error_percent < 5:
    print("✅ PASS: Within 5% of analytical solution")
elif error_percent < 15:
    print("⚠️  WARNING: 5-15% deviation from analytical solution")
else:
    print("❌ FAIL: >15% deviation from analytical solution")
    print()
    print("DEBUGGING INFO:")
    print(f"  Method: {result.method}")
    print(f"  Dynamic pressure: {result.dynamic_pressure:.0f} Pa")
    print(f"  Mach at flutter: {result.mach_number:.3f}")
    print(f"  Reduced frequency: {result.reduced_frequency:.4f}")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
