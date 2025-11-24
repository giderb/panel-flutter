"""Test final fix with both NASTRAN and physics"""

import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Import the modules
sys.path.insert(0, str(Path(__file__).parent))

from python_bridge.integrated_analysis_executor import IntegratedFlutterExecutor

def test_final_fix():
    """Test with NASTRAN enabled"""

    # Simple metallic panel
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
        'use_nastran': True,  # Enable NASTRAN
        'execute_nastran': False  # But use existing F06 file
    }

    # Create executor
    executor = IntegratedFlutterExecutor()

    print("=" * 70)
    print("Testing final fix with NASTRAN + physics...")
    print("=" * 70)

    results = executor.execute_analysis(
        structural_model,
        aero_config,
        config,
        lambda msg, prog: None  # Silent progress
    )

    # Print results
    flutter_speed = results.get('critical_flutter_speed', 0)
    print(f"\nFinal flutter speed: {flutter_speed:.1f} m/s")

    if flutter_speed < 300:
        print("❌ ERROR: Flutter speed is still too low!")
    elif flutter_speed > 1000:
        print("✅ SUCCESS: Flutter speed is reasonable (not spuriously low)")
    else:
        print(f"⚠️  WARNING: Flutter speed {flutter_speed:.1f} m/s seems low but possible")

    return results

if __name__ == "__main__":
    test_final_fix()