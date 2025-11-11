"""Calibrate damping model to match Dowell flutter speed"""

import sys
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from python_bridge.flutter_analyzer import PanelProperties, FlowConditions

# Dowell benchmark panel
panel = PanelProperties(
    length=0.3, width=0.3, thickness=0.0015,
    youngs_modulus=71.7e9, poissons_ratio=0.33,
    density=2810, boundary_conditions='SSSS',
    structural_damping=0.005
)

flow = FlowConditions(mach_number=2.0, altitude=10000)

# Calculate what scale factor gives zero damping at Dowell flutter speed
V_dowell = 1546.82  # m/s (from analytical solution)

# Calculate parameters at flutter
q_flutter = 0.5 * flow.density * V_dowell**2
D = panel.flexural_rigidity()
beta = np.sqrt(flow.mach_number**2 - 1)
lambda_flutter = (q_flutter * panel.length**3) / (D * beta)
lambda_crit = 745.0

print(f"At Dowell flutter speed V = {V_dowell:.1f} m/s:")
print(f"  q = {q_flutter:.1f} Pa")
print(f"  lambda = {lambda_flutter:.1f}")
print(f"  lambda_crit = {lambda_crit:.1f}")
print(f"  lambda/lambda_crit = {lambda_flutter/lambda_crit:.4f}")

# For zero damping: zeta_struct - (lambda_flutter/lambda_crit - 1) * scale = 0
# Therefore: scale = zeta_struct / (lambda_flutter/lambda_crit - 1)

zeta_struct = panel.structural_damping
scale_required = zeta_struct / (lambda_flutter/lambda_crit - 1.0)

print(f"\nRequired scale factor: {scale_required:.6f}")
print(f"Current zeta_struct: {zeta_struct:.6f}")
print(f"Ratio: {scale_required/zeta_struct:.4f}")
