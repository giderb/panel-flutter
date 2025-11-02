"""
Verify PCOMP card format for NASTRAN 2017 compatibility
"""

import sys
from pathlib import Path

def verify_pcomp_format(bdf_file):
    """Verify PCOMP card follows NASTRAN 2017 format."""

    print("="*80)
    print("NASTRAN 2017 PCOMP CARD FORMAT VERIFICATION")
    print("="*80)
    print(f"\nBDF File: {bdf_file}")

    if not Path(bdf_file).exists():
        print(f"\n[ERROR] File not found: {bdf_file}")
        return False

    with open(bdf_file, 'r') as f:
        lines = f.readlines()

    # Find PCOMP card
    pcomp_idx = None
    for i, line in enumerate(lines):
        if line.startswith('PCOMP'):
            pcomp_idx = i
            break

    if pcomp_idx is None:
        print("\n[ERROR] No PCOMP card found in BDF file")
        return False

    print(f"\n[OK] Found PCOMP card at line {pcomp_idx + 1}")

    # Extract PCOMP block
    pcomp_lines = []
    for i in range(pcomp_idx, len(lines)):
        line = lines[i]
        if line.startswith('PCOMP') or line.startswith('+'):
            pcomp_lines.append(line.rstrip('\n'))
        elif line.startswith('$'):
            break
        else:
            break

    print(f"\n[INFO] PCOMP block has {len(pcomp_lines)} lines")
    print("\nPCOMP Card Block:")
    print("-" * 80)
    for i, line in enumerate(pcomp_lines, 1):
        print(f"{i:3}: {line}")
    print("-" * 80)

    # Verify format
    errors = []
    warnings = []

    # Line 1: PCOMP card
    pcomp_line = pcomp_lines[0]

    # Check length (should be 80 chars for fixed format)
    if len(pcomp_line) > 80:
        errors.append(f"Line 1: Too long ({len(pcomp_line)} chars, max 80)")

    # Check if ends with continuation marker
    if not pcomp_line.rstrip().endswith('+1'):
        warnings.append("Line 1: Does not end with +1 continuation marker")

    # Check PID field (positions 8-16)
    try:
        pid_field = pcomp_line[8:16].strip()
        if pid_field:
            pid = int(pid_field)
            print(f"\n[OK] Property ID: {pid}")
    except:
        errors.append("Line 1: Invalid PID field")

    # Continuation lines
    for i, line in enumerate(pcomp_lines[1:], 2):
        if not line.startswith('+'):
            errors.append(f"Line {i}: Should start with continuation marker")
            continue

        # Check continuation marker format
        cont_marker = line[0:8].strip()
        expected_marker = f"+{i-1}"
        if cont_marker != expected_marker:
            warnings.append(f"Line {i}: Continuation marker is '{cont_marker}', expected '{expected_marker}'")

        # Check line length
        if len(line) > 80:
            errors.append(f"Line {i}: Too long ({len(line)} chars, max 80)")

        # Count fields (should be 2 plies = 8 fields + continuation = 9 fields total)
        # Each field is 8 chars, starting after continuation marker (position 8)
        ply_data = line[8:].rstrip()

        # Parse plies (4 fields each: MID, T, THETA, SOUT)
        fields = []
        pos = 8
        while pos < len(line) and pos < 80:
            field = line[pos:pos+8]
            if field.strip() and not field.strip().startswith('+'):
                fields.append(field.strip())
            pos += 8

        num_plies = len(fields) // 4
        print(f"  Line {i}: {num_plies} ply(ies), {len(fields)} fields")

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    if errors:
        print("\n[ERRORS]")
        for err in errors:
            print(f"  ✗ {err}")
    else:
        print("\n[OK] No errors found")

    if warnings:
        print("\n[WARNINGS]")
        for warn in warnings:
            print(f"  ⚠ {warn}")
    else:
        print("\n[OK] No warnings")

    # NASTRAN 2017 specific checks
    print("\n" + "="*80)
    print("NASTRAN 2017 COMPATIBILITY CHECKS")
    print("="*80)

    checks = [
        ("PCOMP card starts line", pcomp_lines[0].startswith('PCOMP')),
        ("PID field present", len(pcomp_lines[0]) >= 16 and pcomp_lines[0][8:16].strip()),
        ("Simple continuation markers (+1, +2)", all(line[0:8].strip() in [f'+{i}' for i in range(1, 100)] for line in pcomp_lines[1:])),
        ("Fixed field format (80 chars max)", all(len(line) <= 80 for line in pcomp_lines)),
        ("Continuation on line 1", pcomp_lines[0].rstrip().endswith('+1')),
    ]

    for check_name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        symbol = "PASS" if passed else "FAIL"
        print(f"  {status} {symbol} {check_name}")

    all_passed = all(check[1] for check in checks) and len(errors) == 0

    print("\n" + "="*80)
    if all_passed:
        print("RESULT: PCOMP card format is NASTRAN 2017 COMPATIBLE [PASS]")
    else:
        print("RESULT: PCOMP card format has ISSUES [FAIL]")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    # Check test BDF
    test_bdf = Path("analysis_output/test_gui_workflow/flutter_analysis.bdf")

    if test_bdf.exists():
        print("Testing generated BDF file...\n")
        verify_pcomp_format(test_bdf)
    else:
        print("Run 'python test_gui_workflow_composite.py' first to generate BDF file")
        sys.exit(1)
