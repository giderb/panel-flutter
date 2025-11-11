"""
Run Python DLM flutter analysis for M=0.8 (metallic example)
"""
import sys
sys.path.insert(0, '.')

from python_bridge.flutter_analyzer import FlutterAnalyzer, PanelProperties, FlowConditions
from models.material import PredefinedMaterials

# Metallic example configuration
# Panel: 500mm × 400mm × 3mm aluminum
aluminum = PredefinedMaterials.aluminum_6061()

panel = PanelProperties(
    length=0.5,      # m
    width=0.4,       # m
    thickness=0.003, # m
    youngs_modulus=aluminum.youngs_modulus,  # 71.7 GPa
    poissons_ratio=aluminum.poissons_ratio,   # 0.33
    density=aluminum.density,                 # 2810 kg/m³
    boundary_conditions='SSSS',  # Fixed parameter name
    structural_damping=0.03  # 3% critical damping
)

flow = FlowConditions(
    mach_number=0.8,
    altitude=10000  # meters
)

print("="*80)
print("PYTHON DLM FLUTTER ANALYSIS - Metallic Example")
print("="*80)
print(f"\nConfiguration:")
print(f"  Panel: {panel.length*1000}x{panel.width*1000}x{panel.thickness*1000} mm")
print(f"  Material: Aluminum 6061-T6")
print(f"  E = {panel.youngs_modulus/1e9:.1f} GPa")
print(f"  rho = {panel.density:.0f} kg/m^3")
print(f"  Mach = {flow.mach_number}")
print(f"  Altitude = {flow.altitude} m")
print(f"  Boundary: {panel.boundary_conditions}")
print(f"  Structural damping: {panel.structural_damping*100:.1f}%")

analyzer = FlutterAnalyzer()

# Run analysis
print(f"\n{'='*80}")
print("Running flutter analysis...")
print(f"{'='*80}\n")

result = analyzer.analyze(
    panel=panel,
    flow=flow,
    method='auto',  # Will select DLM for M=0.8
    validate=True,
    velocity_range=(100, 800),
    velocity_points=30
)

print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}")
print(f"  Method used: {result.method}")
print(f"  Flutter speed: {result.flutter_speed:.2f} m/s")
print(f"  Flutter frequency: {result.flutter_frequency:.2f} Hz")
print(f"  Flutter mode: {result.flutter_mode}")
print(f"  Reduced frequency: {result.reduced_frequency:.4f}")
print(f"  Converged: {result.converged}")
print(f"  Validation: {result.validation_status}")

# Calculate analytical comparison
import math
D = panel.youngs_modulus * panel.thickness**3 / (12 * (1 - panel.poissons_ratio**2))
m = panel.density * panel.thickness
omega_11 = math.pi**2 * math.sqrt(D/m) * ((1/panel.length)**2 + (1/panel.width)**2)
f_11 = omega_11 / (2 * math.pi)

print(f"\n{'='*80}")
print("ANALYTICAL COMPARISON")
print(f"{'='*80}")
print(f"  Classical plate theory:")
print(f"    First mode frequency: {f_11:.2f} Hz")
print(f"    Python result: {result.flutter_frequency:.2f} Hz")
print(f"    Error: {abs(f_11 - result.flutter_frequency)/f_11*100:.1f}%")

# Calculate reduced frequency
k = result.reduced_frequency if hasattr(result, 'reduced_frequency') else 0.3
V_analytical = omega_11 * panel.length / k
print(f"\n  Flutter speed (k={k:.2f}):")
print(f"    Analytical estimate: {V_analytical:.1f} m/s")
print(f"    Python result: {result.flutter_speed:.1f} m/s")
print(f"    Difference: {abs(V_analytical - result.flutter_speed):.1f} m/s")

print(f"\n{'='*80}")
print("CERTIFICATION ASSESSMENT")
print(f"{'='*80}")

if result.converged:
    print("  ✓ Analysis converged")
else:
    print("  ✗ Analysis did not converge")

if abs(f_11 - result.flutter_frequency)/f_11 < 0.05:
    print(f"  ✓ Frequency error <5% (actual: {abs(f_11 - result.flutter_frequency)/f_11*100:.1f}%)")
else:
    print(f"  ✗ Frequency error >5% (actual: {abs(f_11 - result.flutter_frequency)/f_11*100:.1f}%)")

if 250 <= result.flutter_speed <= 600:
    print(f"  ✓ Flutter speed in expected range (250-600 m/s)")
else:
    print(f"  ⚠ Flutter speed outside expected range: {result.flutter_speed:.1f} m/s")

print(f"\n{'='*80}\n")
