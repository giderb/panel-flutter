"""Test to debug why flutter speed shows as 100 m/s"""

import sys
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Import the modules
sys.path.insert(0, str(Path(__file__).parent))
from python_bridge.integrated_analysis_executor import IntegratedFlutterExecutor

def test_flutter_analysis():
    """Test flutter analysis to see what's returned"""

    # Load the berkuk project data
    project_file = Path(__file__).parent / "projects" / "20251111_174830_bberkuk.json"

    with open(project_file, 'r') as f:
        project_data = json.load(f)

    # Create structural model
    structural_model = project_data.get('structural_model', {})

    # Create aerodynamic config
    aero_config = project_data.get('aerodynamic_config', {})

    # Analysis config
    config = {
        'n_modes': 15,
        'mesh_nx': 10,
        'mesh_ny': 10,
        'velocity_min': 100.0,
        'velocity_max': 4500.0,
        'velocity_points': 50,
        'working_dir': Path.cwd() / 'analysis_output',
        'use_nastran': True,
        'execute_nastran': True
    }

    # Create executor
    executor = IntegratedFlutterExecutor()

    # Run analysis
    print("=" * 70)
    print("Running flutter analysis...")
    print("=" * 70)

    results = executor.execute_analysis(
        structural_model,
        aero_config,
        config,
        lambda msg, prog: print(f"Progress: {msg} ({prog*100:.0f}%)")
    )

    # Print results
    print("=" * 70)
    print("ANALYSIS RESULTS:")
    print("=" * 70)
    print(f"Success: {results.get('success')}")
    print(f"Converged: {results.get('converged')}")
    print(f"Critical flutter speed: {results.get('critical_flutter_speed')}")
    print(f"Critical flutter frequency: {results.get('critical_flutter_frequency')}")
    print(f"Critical flutter mode: {results.get('critical_flutter_mode')}")

    # Check physics result
    physics_result = results.get('physics_result', {})
    print(f"\nPhysics result flutter speed: {physics_result.get('flutter_speed')}")

    # Check NASTRAN result
    nastran_result = results.get('nastran_result', {})
    print(f"NASTRAN result flutter speed: {nastran_result.get('flutter_speed')}")

    print("=" * 70)

    return results

if __name__ == "__main__":
    test_flutter_analysis()