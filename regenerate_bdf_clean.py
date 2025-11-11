"""Clean BDF regeneration with no cached imports"""
import sys
import os

# Remove any cached imports
if 'python_bridge' in sys.modules:
    del sys.modules['python_bridge']
if 'python_bridge.bdf_generator_sol145_fixed' in sys.modules:
    del sys.modules['python_bridge.bdf_generator_sol145_fixed']

sys.path.insert(0, '.')

from python_bridge.bdf_generator_sol145_fixed import Sol145BDFGenerator, PanelConfig, MaterialConfig, AeroConfig

print("Generating corrected BDF...")

panel = PanelConfig(
    length=500.0,
    width=400.0,
    thickness=3.0,
    nx=10,
    ny=10
)

material = MaterialConfig(
    youngs_modulus=71700.0,
    poissons_ratio=0.33,
    density=2.81e-6,
    shear_modulus=None
)

aero = AeroConfig(
    mach_number=0.8,
    reference_velocity=1.0,
    reference_chord=500.0,
    reference_density=1.225e-9,
    altitude=10000,
    velocities=[float(v) for v in range(100000, 800001, 35000)]
)

gen = Sol145BDFGenerator()
filepath = gen.generate_bdf(
    panel=panel,
    material=material,
    aero=aero,
    boundary_conditions='SSSS',
    n_modes=20,
    output_filename='flutter_CORRECTED.bdf',
    aerodynamic_theory='auto'
)

print(f"Generated: {filepath}")

# Verify PSHELL formatting
with open('flutter_CORRECTED.bdf', 'r') as f:
    content = f.read()

for line in content.split('\n'):
    if line.startswith('PSHELL'):
        print(f"\nPSHELL line: {repr(line)}")
        print(f"Length: {len(line)}")

        # Check fields
        fields = [line[i*8:(i+1)*8] if i*8 < len(line) else '' for i in range(6)]
        print("\nFields:")
        field_names = ['Card', 'PID', 'MID1', 'T', 'MID2', '12I/T^3']
        for i, (name, field) in enumerate(zip(field_names, fields)):
            print(f"  {i+1} ({name:8s}): {repr(field)}")

        # Verify MID2
        if len(line) >= 40:
            mid2_field = line[32:40]
            print(f"\nMID2 field (bytes 32-40): {repr(mid2_field)}")
            if mid2_field.strip() == '1':
                print("PASS: MID2=1 in correct position")
            else:
                print(f"FAIL: MID2 field is '{mid2_field.strip()}'")
        else:
            print(f"\nFAIL: Line too short ({len(line)} chars, need >= 40)")
        break

# Verify other critical cards
print("\n" + "="*60)
print("Verification of critical cards:")
print("="*60)

if 'PARAM   W3      0.03' in content:
    print("PASS: PARAM W3 0.03 present")
else:
    print("FAIL: PARAM W3 missing")

if 'MAT1    1       71700.0' in content and '2.81E-06' in content:
    print("PASS: MAT1 correct (E=71700 MPa, rho=2.81e-6 kg/mm^3)")
else:
    print("FAIL: MAT1 incorrect")

if 'TABDMP1' in content:
    print("PASS: TABDMP1 present (backup damping)")
else:
    print("WARN: TABDMP1 not present")

print("\n" + "="*60)
print("BDF generation complete")
print("="*60)
