"""Debug damping calculation to find why flutter bracket is not detected"""

import sys
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from python_bridge.flutter_analyzer import FlutterAnalyzer, PanelProperties, FlowConditions

# Dowell benchmark panel
panel = PanelProperties(
    length=0.3, width=0.3, thickness=0.0015,
    youngs_modulus=71.7e9, poissons_ratio=0.33,
    density=2810, boundary_conditions='SSSS',
    structural_damping=0.005
)

flow = FlowConditions(mach_number=2.0, altitude=10000)

analyzer = FlutterAnalyzer()

# Calculate Dowell estimate
dowell_flutter = analyzer._calculate_dowell_flutter_speed(panel, flow)
print(f"Dowell analytical flutter speed: {dowell_flutter:.1f} m/s")

# Test damping at velocities around Dowell estimate
test_velocities_coarse = np.linspace(1000, 2000, 30)  # Match test case
test_velocities_fine = np.linspace(1500, 1600, 50)  # Fine near expected flutter

print("\nDamping values for Mode 0 (COARSE GRID):")
print("Velocity (m/s)  |  Damping (1/s)")
print("-" * 40)

for v in test_velocities_coarse:
    damping = analyzer._compute_modal_damping(panel, flow, v, 'piston', mode_idx=0)
    marker = " <-- ZERO" if abs(damping) < 0.5 else ""
    sign_str = "+" if damping > 0 else "-"
    print(f"{v:8.1f}       |  {sign_str}{abs(damping):11.3e}{marker}")

print("\n\nFINE GRID near expected flutter:")
print("Velocity (m/s)  |  Damping (1/s)")
print("-" * 40)

for v in test_velocities_fine:
    damping = analyzer._compute_modal_damping(panel, flow, v, 'piston', mode_idx=0)
    marker = " <-- ZERO" if abs(damping) < 0.1 else ""
    sign_str = "+" if damping > 0 else "-"
    print(f"{v:8.1f}       |  {sign_str}{abs(damping):11.3e}{marker}")

print(f"\nExpected flutter around: {dowell_flutter:.1f} m/s")
