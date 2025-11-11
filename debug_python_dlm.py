"""Debug Python DLM flutter detection for M=0.8"""
import sys
sys.path.insert(0, '.')

import numpy as np
import math
from python_bridge.flutter_analyzer import FlutterAnalyzer, PanelProperties, FlowConditions
from models.material import PredefinedMaterials

print("="*80)
print("PYTHON DLM DEBUG - M=0.8 METALLIC PANEL")
print("="*80)

aluminum = PredefinedMaterials.aluminum_6061()

panel = PanelProperties(
    length=0.5,
    width=0.4,
    thickness=0.003,
    youngs_modulus=aluminum.youngs_modulus,
    poissons_ratio=aluminum.poissons_ratio,
    density=aluminum.density,
    boundary_conditions='SSSS',
    structural_damping=0.03
)

flow = FlowConditions(
    mach_number=0.8,
    altitude=10000
)

# Calculate expected first mode frequency
D = panel.youngs_modulus * panel.thickness**3 / (12 * (1 - panel.poissons_ratio**2))
m_surface = panel.density * panel.thickness
omega_11 = math.pi**2 * math.sqrt(D/m_surface) * ((1/panel.length)**2 + (1/panel.width)**2)
f_11 = omega_11 / (2 * math.pi)

print(f"\nPanel: {panel.length}m x {panel.width}m x {panel.thickness}m")
print(f"Material: Aluminum 6061-T6")
print(f"E = {panel.youngs_modulus/1e9:.1f} GPa")
print(f"rho = {panel.density:.0f} kg/m^3")
print(f"Boundary: {panel.boundary_conditions}")
print(f"Flow: M = {flow.mach_number}, Alt = {flow.altitude}m")
print(f"\nExpected f11 = {f_11:.2f} Hz")

print("\n" + "="*80)
print("Running DLM flutter analysis with extended velocity range...")
print("="*80)

analyzer = FlutterAnalyzer()

# Test with wider velocity range
print(f"\nTest: velocity range 50-1200 m/s (60 points)")
print("-" * 80)

try:
    result = analyzer.analyze(
        panel=panel,
        flow=flow,
        method='doublet',
        validate=False,
        velocity_range=(50, 1200),
        velocity_points=60
    )

    print(f"Result: V_flutter = {result.flutter_speed:.1f} m/s")
    print(f"        f_flutter = {result.flutter_frequency:.2f} Hz")
    print(f"        mode = {result.flutter_mode}")
    print(f"        k = {result.reduced_frequency:.4f}")

    if result.flutter_speed < 9000:
        print(f">>> FLUTTER FOUND at {result.flutter_speed:.1f} m/s <<<")
    else:
        print(">>> Flutter not found in this range")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Dowell estimate
print("\n" + "="*80)
print("Analytical Flutter Speed Estimate (Dowell)")
print("="*80)

k_typical = 0.3
V_dowell = omega_11 * panel.length / k_typical
print(f"Using typical k = {k_typical}")
print(f"Dowell estimate: V_flutter approx {V_dowell:.1f} m/s")
print(f"Expected range: {V_dowell*0.7:.1f} - {V_dowell*1.3:.1f} m/s")

print("="*80)
