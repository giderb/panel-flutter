"""Test F06 parser on the current analysis output"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from python_bridge.f06_parser import F06Parser

f06_path = Path("analysis_output/flutter_analysis.f06")

print("=" * 80)
print("TESTING F06 PARSER")
print("=" * 80)
print(f"F06 file: {f06_path}")
print()

parser = F06Parser(f06_path)
results = parser.parse()

print("PARSE RESULTS:")
print(f"  Success: {results.get('success')}")
print(f"  Errors: {results.get('errors')}")
print(f"  Warnings: {results.get('warnings')}")
print(f"  Flutter points found: {len(results.get('flutter_results', []))}")
print(f"  Critical flutter velocity: {results.get('critical_flutter_velocity')}")
print(f"  Critical flutter frequency: {results.get('critical_flutter_frequency')}")
print()

if results.get('critical_flutter_velocity'):
    print(f"[OK] FLUTTER DETECTED: {results['critical_flutter_velocity']:.1f} m/s")
else:
    print("[FAIL] NO FLUTTER DETECTED")

print("=" * 80)
