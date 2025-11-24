"""Simple test to find where 100 m/s comes from"""

import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Import the modules
sys.path.insert(0, str(Path(__file__).parent))

# Test the F06 parser directly
from python_bridge.f06_parser import F06Parser

# Parse the latest F06 file
f06_file = Path("analysis_output/flutter_analysis.f06")
if f06_file.exists():
    print(f"Parsing {f06_file}")
    parser = F06Parser(f06_file)
    results = parser.parse()

    print("\n" + "="*70)
    print("F06 PARSER RESULTS:")
    print("="*70)
    print(f"success: {results.get('success')}")
    print(f"flutter_found: {results.get('flutter_found')}")
    print(f"critical_flutter_velocity: {results.get('critical_flutter_velocity')} m/s")
    print(f"critical_flutter_frequency: {results.get('critical_flutter_frequency')} Hz")

    # Check flutter points
    flutter_points = results.get('flutter_results', [])
    if flutter_points:
        print(f"\nFound {len(flutter_points)} flutter points")
        # Show first few
        for i, pt in enumerate(flutter_points[:5]):
            print(f"  Point {i+1}: V={pt.velocity/1000:.1f} m/s, g={pt.damping:.6f}, f={pt.frequency:.1f} Hz")
else:
    print(f"F06 file not found: {f06_file}")