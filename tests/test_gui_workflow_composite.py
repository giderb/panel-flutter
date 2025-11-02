"""
Test composite material workflow from GUI to BDF generation
This test mimics the actual GUI workflow to verify the bug fix
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from models.material import OrthotropicMaterial, CompositeLaminate, CompositeLamina
from models.structural import StructuralModel, PanelGeometry, BoundaryCondition
from python_bridge.integrated_analysis_executor import IntegratedFlutterExecutor

def test_gui_composite_workflow():
    """Test the actual GUI workflow with composite materials"""
    print("\n" + "="*80)
    print("TEST: GUI COMPOSITE WORKFLOW (Bug Fix Verification)")
    print("="*80)

    # Step 1: Create composite material (as GUI does)
    print("\n[1] Creating composite materials...")

    im7_8552 = OrthotropicMaterial(
        id=1,
        name="IM7/8552",
        e1=171e9,  # 171 GPa
        e2=9.08e9,  # 9.08 GPa
        nu12=0.32,
        g12=5.29e9,  # 5.29 GPa
        density=1570,  # kg/m³
        g1z=5.29e9,
        g2z=3.0e9
    )

    # Create composite laminate [0/90]s
    laminas = [
        CompositeLamina(1, im7_8552, 0.125, 0),      # 0° ply
        CompositeLamina(2, im7_8552, 0.125, 90),     # 90° ply
        CompositeLamina(3, im7_8552, 0.125, 90),     # 90° ply
        CompositeLamina(4, im7_8552, 0.125, 0),      # 0° ply
    ]

    laminate = CompositeLaminate(
        id=1,
        name="IM7 [0/90]s",
        laminas=laminas,
        description="Symmetric cross-ply laminate"
    )

    print(f"[OK] Created composite: {laminate.name}")
    print(f"  - Number of plies: {len(laminate.laminas)}")
    print(f"  - Total thickness: {laminate.total_thickness} mm")

    # Step 2: Create structural model (as GUI does)
    print("\n[2] Creating structural model...")

    structural_model = StructuralModel(model_id=1, name="Test Structure")

    # Set geometry
    geometry = PanelGeometry(
        length=1.0,     # 1m
        width=0.8,      # 0.8m
        thickness=0.0005  # 0.5mm (will be overridden by composite)
    )
    structural_model.set_geometry(geometry)

    # Add material to structural model (GUI uses add_material which adds to materials list)
    structural_model.add_material(laminate)

    print(f"[OK] Created structural model: {structural_model.name}")
    print(f"  - Geometry: {geometry.length}m x {geometry.width}m")
    print(f"  - Materials count: {len(structural_model.materials)}")
    print(f"  - Material type: {type(structural_model.materials[0]).__name__}")

    # Step 3: Create aerodynamic model
    print("\n[3] Creating aerodynamic configuration...")

    aero_config = {
        'flow_conditions': {
            'mach_number': 3.0,
            'altitude': 15000,
            'temperature': None,
            'pressure': None,
            'density': None
        },
        'theory': 'PISTON_THEORY'
    }

    print(f"[OK] Aerodynamic config: M={aero_config['flow_conditions']['mach_number']}")

    # Step 4: Execute analysis (as GUI does)
    print("\n[4] Running integrated analysis...")

    # Set a dummy NASTRAN path so BDF generation occurs
    executor = IntegratedFlutterExecutor(nastran_path="dummy_path")

    config = {
        'velocity_min': 500,
        'velocity_max': 1200,
        'velocity_points': 8,
        'mesh_nx': 10,
        'mesh_ny': 10,
        'n_modes': 10,
        'use_nastran': True,
        'execute_nastran': False,  # Just generate BDF, don't run
        'working_dir': Path('analysis_output/test_gui_workflow')
    }

    # Create output directory
    config['working_dir'].mkdir(parents=True, exist_ok=True)

    def progress(msg, pct):
        print(f"  [{pct*100:3.0f}%] {msg}")

    try:
        results = executor.execute_analysis(
            structural_model,
            aero_config,
            config,
            progress_callback=progress
        )

        print(f"\n[OK] Analysis completed: {results.get('success')}")

    except Exception as e:
        print(f"\n[FAIL] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Verify BDF file has composite materials
    print("\n[5] Verifying BDF file...")

    bdf_file = config['working_dir'] / 'flutter_analysis.bdf'

    if not bdf_file.exists():
        print(f"[FAIL] BDF file not found: {bdf_file}")
        return False

    print(f"[OK] BDF file exists: {bdf_file}")

    # Read BDF content
    with open(bdf_file, 'r') as f:
        bdf_content = f.read()

    # Verify composite-specific content
    checks = [
        ("MAT8", "MAT8 card for orthotropic material"),
        ("PCOMP", "PCOMP card for composite property"),
        ("IM7/8552", "Material name in comments"),
        ("[0/90]s", "Stacking sequence in comments"),
        ("171000", "E1 value (171 GPa in MPa)"),
        ("9080", "E2 value (9.08 GPa in MPa)"),
        ("0.320", "Poisson's ratio"),
    ]

    all_passed = True
    for keyword, description in checks:
        if keyword in bdf_content:
            print(f"  [OK] Found {description}")
        else:
            print(f"  [FAIL] Missing {description}")
            all_passed = False

    # Check that MAT1/PSHELL are NOT present (should only have MAT8/PCOMP)
    if "MAT1" in bdf_content and "MAT8" in bdf_content:
        print(f"  [WARN] Found both MAT1 and MAT8 (should only have MAT8)")
    elif "MAT1" in bdf_content:
        print(f"  [FAIL] Found MAT1 instead of MAT8 for composite")
        all_passed = False
    else:
        print(f"  [OK] No MAT1 card (correctly using MAT8)")

    if "PSHELL" in bdf_content:
        print(f"  [FAIL] Found PSHELL instead of PCOMP for composite")
        all_passed = False
    else:
        print(f"  [OK] No PSHELL card (correctly using PCOMP)")

    # Print sample of generated cards
    print("\n[6] Sample of generated composite cards:")
    lines = bdf_content.split('\n')
    in_mat_section = False
    card_count = 0
    for line in lines:
        if 'Composite' in line or 'Orthotropic' in line:
            in_mat_section = True
        if in_mat_section and card_count < 10:
            if line.strip() and (not line.startswith('$') or 'Composite' in line or 'Material' in line):
                print(f"  {line}")
                if not line.startswith('$'):
                    card_count += 1
        if line.startswith('$ Grid Points'):
            break

    # Final verdict
    print("\n" + "="*80)
    if all_passed:
        print("[SUCCESS] GUI WORKFLOW TEST PASSED")
        print("="*80)
        print("\nThe bug fix is working correctly!")
        print(f"[OK] Composite materials from GUI are correctly written to BDF")
        print(f"[OK] MAT8/PCOMP cards generated instead of MAT1/PSHELL")
        print(f"[OK] Material properties are correct (E1={checks[4][0]} MPa, etc.)")
        print(f"\nBDF file: {bdf_file}")
        return True
    else:
        print("[FAILURE] GUI WORKFLOW TEST FAILED")
        print("="*80)
        print("\nSome checks failed. Review the output above.")
        return False


if __name__ == "__main__":
    success = test_gui_composite_workflow()
    sys.exit(0 if success else 1)
