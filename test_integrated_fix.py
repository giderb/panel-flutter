"""Test integrated fix for flutter speed display"""

import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Import the modules
sys.path.insert(0, str(Path(__file__).parent))

from python_bridge.integrated_analysis_executor import IntegratedFlutterExecutor

def test_integrated_analysis():
    """Test the integrated analysis with the fix"""

    # Simple test config
    structural_model = {
        'panel': {
            'length': 0.45,
            'width': 0.4,
            'thickness': 0.00589
        },
        'material': {
            'youngs_modulus': 71.7e9,
            'density': 2810,
            'poissons_ratio': 0.33
        }
    }

    aero_config = {
        'flow_conditions': {
            'mach_number': 1.27,
            'altitude': 0,
            'temperature': 288.15,
            'pressure': 101325,
            'density': 1.225
        }
    }

    config = {
        'n_modes': 15,
        'mesh_nx': 10,
        'mesh_ny': 10,
        'velocity_min': 100.0,
        'velocity_max': 4500.0,
        'velocity_points': 50,
        'working_dir': Path.cwd() / 'analysis_output',
        'use_nastran': False,  # Just use physics for quick test
        'execute_nastran': False
    }

    # Create executor
    executor = IntegratedFlutterExecutor()

    # Run analysis
    print("=" * 70)
    print("Running integrated flutter analysis (physics only)...")
    print("=" * 70)

    results = executor.execute_analysis(
        structural_model,
        aero_config,
        config,
        lambda msg, prog: print(f"Progress: {msg} ({prog*100:.0f}%)")
    )

    # Print results
    print("\n" + "=" * 70)
    print("INTEGRATED ANALYSIS RESULTS:")
    print("=" * 70)
    print(f"Success: {results.get('success')}")
    print(f"Converged: {results.get('converged')}")
    print(f"Critical flutter speed: {results.get('critical_flutter_speed')} m/s")
    print(f"Critical flutter frequency: {results.get('critical_flutter_frequency')} Hz")
    print("=" * 70)

    # Check if the value is reasonable (not 100 m/s)
    flutter_speed = results.get('critical_flutter_speed', 0)
    if flutter_speed and abs(flutter_speed - 100) < 1:
        print("\n⚠️  ERROR: Flutter speed is still showing as 100 m/s!")
    elif flutter_speed and flutter_speed > 1000:
        print(f"\n✅ SUCCESS: Flutter speed is {flutter_speed:.1f} m/s (not 100 m/s)")
    else:
        print(f"\n❓ UNCLEAR: Flutter speed is {flutter_speed:.1f} m/s")

    return results

if __name__ == "__main__":
    test_integrated_analysis()