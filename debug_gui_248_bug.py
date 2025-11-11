"""
Debug script to trace the 248 m/s bug in GUI workflow
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from python_bridge.f06_parser import F06Parser

def main():
    """Debug F06 parsing to find where 248 m/s comes from"""

    f06_path = Path("C:/Users/giderb/PycharmProjects/panel-flutter/analysis_output/flutter_analysis.f06")

    if not f06_path.exists():
        print(f"ERROR: F06 file not found at {f06_path}")
        return

    print("="*70)
    print("DEBUGGING GUI 248 M/S BUG")
    print("="*70)

    # Parse F06
    parser = F06Parser(f06_path)
    results = parser.parse()

    print(f"\nParse success: {results['success']}")
    print(f"Errors: {results['errors']}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Modal frequencies found: {len(results['modal_frequencies'])}")
    print(f"Flutter points found: {len(results['flutter_results'])}")

    # Show critical flutter velocity
    print(f"\nCritical flutter velocity: {results['critical_flutter_velocity']}")
    print(f"Critical flutter frequency: {results['critical_flutter_frequency']}")

    # Group flutter points by velocity and show damping trends
    from collections import defaultdict
    velocity_groups = defaultdict(list)

    for pt in results['flutter_results']:
        velocity_groups[pt.velocity].append(pt)

    sorted_velocities = sorted(velocity_groups.keys())

    print(f"\n{'='*70}")
    print("FLUTTER DATA ANALYSIS")
    print(f"{'='*70}")
    print(f"Velocity range: {min(sorted_velocities)/1000:.1f} - {max(sorted_velocities)/1000:.1f} m/s")
    print(f"Number of velocity points: {len(sorted_velocities)}")

    # Show modes with frequency in realistic panel flutter range (5-100 Hz)
    print(f"\n{'Velocity (m/s)':<15} {'Min Damping':<15} {'Freq at Min (Hz)':<20}")
    print("-"*70)

    for v in sorted_velocities:
        modes = velocity_groups[v]
        # Filter for realistic panel flutter modes
        panel_modes = [m for m in modes if 5.0 <= m.frequency <= 100.0]

        if panel_modes:
            min_damping_mode = min(panel_modes, key=lambda m: m.damping)
            print(f"{v/1000:>13.1f}   {min_damping_mode.damping:>13.4f}   {min_damping_mode.frequency:>18.2f}")

    # Look for damping sign changes
    print(f"\n{'='*70}")
    print("LOOKING FOR FLUTTER (DAMPING SIGN CHANGE)")
    print(f"{'='*70}")

    for i in range(len(sorted_velocities) - 1):
        v1 = sorted_velocities[i]
        v2 = sorted_velocities[i + 1]

        modes_v1 = [m for m in velocity_groups[v1] if 5.0 <= m.frequency <= 100.0]
        modes_v2 = [m for m in velocity_groups[v2] if 5.0 <= m.frequency <= 100.0]

        # Try to match modes by frequency
        for m1 in modes_v1:
            for m2 in modes_v2:
                # Check if same mode (frequency within 20%)
                freq_ratio = abs(m2.frequency - m1.frequency) / m1.frequency if m1.frequency > 0 else float('inf')
                if freq_ratio < 0.2:
                    # Check for damping sign change
                    if m1.damping < 0 and m2.damping > 0:
                        print(f"\nFOUND FLUTTER TRANSITION:")
                        print(f"  V1 = {v1/1000:.1f} m/s: damping = {m1.damping:.6f}, freq = {m1.frequency:.2f} Hz")
                        print(f"  V2 = {v2/1000:.1f} m/s: damping = {m2.damping:.6f}, freq = {m2.frequency:.2f} Hz")

                        # Linear interpolation
                        t = -m1.damping / (m2.damping - m1.damping)
                        v_flutter = v1 + t * (v2 - v1)
                        f_flutter = m1.frequency + t * (m2.frequency - m1.frequency)

                        print(f"  INTERPOLATED: V_flutter = {v_flutter/1000:.1f} m/s, f = {f_flutter:.2f} Hz")

    # Show all damping values
    print(f"\n{'='*70}")
    print("ALL DAMPING VALUES (for modes 5-100 Hz)")
    print(f"{'='*70}")

    for v in sorted_velocities:
        modes = [m for m in velocity_groups[v] if 5.0 <= m.frequency <= 100.0]
        print(f"\nVelocity = {v/1000:.1f} m/s:")
        for m in sorted(modes, key=lambda x: x.frequency):
            sign = "POS" if m.damping > 0 else "NEG" if m.damping < 0 else "ZERO"
            print(f"  f={m.frequency:6.2f} Hz, g={m.damping:10.6f} [{sign}]")

    print(f"\n{'='*70}")
    print("DIAGNOSIS")
    print(f"{'='*70}")

    if results['critical_flutter_velocity'] is None:
        print("NO FLUTTER DETECTED in velocity range tested")
        print("Recommendation: INCREASE velocity range or use Python DLM results")
    else:
        print(f"Flutter detected at {results['critical_flutter_velocity']/1000:.1f} m/s")

if __name__ == "__main__":
    main()
