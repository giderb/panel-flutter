"""Find positive damping in F06 file"""
import re

with open('analysis_output/flutter_analysis.f06', 'r') as f:
    lines = f.readlines()

print("Looking for positive damping values...")
positive_found = False
for line in lines:
    # Look for lines with numerical data (flutter table format)
    parts = line.split()
    if len(parts) >= 7:
        try:
            # Check if third column is velocity (E+05 format)
            if 'E+05' in parts[2]:
                velocity = float(parts[2])
                damping = float(parts[3])
                freq = float(parts[4])

                if damping > 0:
                    print(f"POSITIVE DAMPING: V={velocity/1000:.1f} m/s, g={damping:.6f}, f={freq:.1f} Hz")
                    positive_found = True
                    if positive_found and velocity/1000 < 200:  # First few positive dampings
                        print(f"  Line: {line.strip()}")
        except (ValueError, IndexError):
            continue

if not positive_found:
    print("No positive damping found in F06 file")