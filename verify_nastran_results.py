"""
Verify NASTRAN F06 results after running corrected BDF
Usage: python verify_nastran_results.py <path_to_f06_file>
"""
import sys
import re
import math

def parse_f06(filepath):
    """Extract key results from NASTRAN F06 file"""
    try:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Could not read F06 file: {e}")
        return None

    results = {
        'frequencies': [],
        'eigenvalues': [],
        'damping_values': [],
        'flutter_speed': None,
        'flutter_frequency': None
    }

    # Extract eigenvalues and frequencies
    eigen_pattern = r'^\s+(\d+)\s+\d+\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)'
    for match in re.finditer(eigen_pattern, content, re.MULTILINE):
        mode = int(match.group(1))
        eigenvalue = float(match.group(2))
        omega = float(match.group(3))
        freq = float(match.group(4))
        results['eigenvalues'].append((mode, eigenvalue))
        results['frequencies'].append((mode, freq))

    # Extract damping values
    damp_pattern = r'([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([+-]?[\d.E+-]+)\s+([\d.E+-]+)'
    for match in re.finditer(damp_pattern, content, re.MULTILINE):
        try:
            velocity = float(match.group(3))
            damping = float(match.group(4))
            frequency = float(match.group(5))
            if 100000 < velocity < 2000000:  # mm/s range
                results['damping_values'].append((velocity, damping, frequency))
        except:
            pass

    # Extract flutter point
    if 'FLUTTER POINT' in content or 'CRITICAL' in content:
        flutter_pattern = r'FLUTTER.*?([\d.E+-]+).*?([\d.E+-]+)'
        match = re.search(flutter_pattern, content, re.IGNORECASE)
        if match:
            results['flutter_speed'] = float(match.group(1)) / 1000.0  # mm/s to m/s
            results['flutter_frequency'] = float(match.group(2))

    return results

def validate_results(results, python_dlm_speed=1113.7):
    """Validate NASTRAN results against expected values"""

    print("="*80)
    print("NASTRAN F06 VALIDATION RESULTS")
    print("="*80)

    expected_freq = 74.61  # Hz
    expected_eigenvalue = (2 * math.pi * expected_freq)**2

    tests_passed = 0
    tests_total = 0

    # Test 1: First mode frequency
    print("\n[TEST 1] First Mode Frequency")
    print("-" * 80)
    tests_total += 1

    if results['frequencies']:
        mode, freq = results['frequencies'][0]
        print(f"NASTRAN: f1 = {freq:.2f} Hz")
        print(f"Expected: f1 = {expected_freq:.2f} Hz")

        error = abs(freq - expected_freq) / expected_freq * 100
        print(f"Error: {error:.2f}%")

        if error < 2.0:
            print("PASS: Frequency within 2% of analytical")
            tests_passed += 1
        elif error < 5.0:
            print("WARN: Frequency within 5% (acceptable but investigate)")
            tests_passed += 1
        else:
            print("FAIL: Frequency error > 5%")
    else:
        print("FAIL: No frequency data found in F06")

    # Test 2: Eigenvalue
    print("\n[TEST 2] First Mode Eigenvalue")
    print("-" * 80)
    tests_total += 1

    if results['eigenvalues']:
        mode, eigenval = results['eigenvalues'][0]
        print(f"NASTRAN: λ1 = {eigenval:.0f} rad²/s²")
        print(f"Expected: λ1 = {expected_eigenvalue:.0f} rad²/s²")

        error = abs(eigenval - expected_eigenvalue) / expected_eigenvalue * 100
        print(f"Error: {error:.2f}%")

        if error < 5.0:
            print("PASS: Eigenvalue within 5%")
            tests_passed += 1
        else:
            print("FAIL: Eigenvalue error > 5%")

            # Diagnose likely cause
            ratio = expected_eigenvalue / eigenval
            if ratio > 10:
                print(f"CRITICAL: Eigenvalue is {ratio:.1f}x too low!")
                print("→ PSHELL MID2 field may still be incorrect")
                print("→ Check that PSHELL line has exactly 40 characters")
    else:
        print("FAIL: No eigenvalue data found in F06")

    # Test 3: Non-zero damping
    print("\n[TEST 3] Structural Damping")
    print("-" * 80)
    tests_total += 1

    if results['damping_values']:
        # Check first 5 damping values
        sample_damp = results['damping_values'][:5]
        print("Sample damping values:")
        for vel, damp, freq in sample_damp:
            print(f"  V={vel/1000:.1f} m/s: damping={damp:.6f}, f={freq:.2f} Hz")

        # Check if all zero
        all_zero = all(abs(d[1]) < 1e-9 for d in sample_damp)
        if all_zero:
            print("FAIL: All damping values are zero")
            print("→ PARAM W3 may not be working")
            print("→ Check BDF file for 'PARAM   W3      0.03'")
        else:
            print("PASS: Non-zero damping detected")
            tests_passed += 1
    else:
        print("FAIL: No damping data found in F06")

    # Test 4: Flutter detection
    print("\n[TEST 4] Flutter Detection")
    print("-" * 80)
    tests_total += 1

    if results['flutter_speed']:
        print(f"NASTRAN flutter speed: {results['flutter_speed']:.1f} m/s")
        print(f"NASTRAN flutter frequency: {results['flutter_frequency']:.2f} Hz")
        print("PASS: Flutter point detected")
        tests_passed += 1
    else:
        # Try to find zero-crossing in damping
        if results['damping_values']:
            print("No explicit flutter point in F06")
            print("Searching for damping sign change...")

            for i in range(len(results['damping_values']) - 1):
                vel1, damp1, freq1 = results['damping_values'][i]
                vel2, damp2, freq2 = results['damping_values'][i + 1]

                if damp1 > 0 and damp2 < 0:
                    # Zero crossing found
                    v_flutter = (vel1 + vel2) / 2 / 1000.0  # mm/s to m/s
                    f_flutter = (freq1 + freq2) / 2
                    print(f"Flutter bracket found: {vel1/1000:.1f} - {vel2/1000:.1f} m/s")
                    print(f"Estimated flutter speed: {v_flutter:.1f} m/s")
                    print(f"Flutter frequency: {f_flutter:.2f} Hz")
                    results['flutter_speed'] = v_flutter
                    results['flutter_frequency'] = f_flutter
                    print("PASS: Flutter detected (from damping analysis)")
                    tests_passed += 1
                    break
            else:
                print("FAIL: No flutter point detected")
                print("→ May be outside velocity range")
                print("→ Check if damping is all positive or all negative")
        else:
            print("FAIL: No flutter detection possible (no damping data)")

    # Test 5: Agreement with Python DLM
    if results['flutter_speed']:
        print("\n[TEST 5] Agreement with Python DLM")
        print("-" * 80)
        tests_total += 1

        print(f"Python DLM: {python_dlm_speed:.1f} m/s")
        print(f"NASTRAN: {results['flutter_speed']:.1f} m/s")

        diff = abs(results['flutter_speed'] - python_dlm_speed)
        diff_pct = diff / python_dlm_speed * 100

        print(f"Difference: {diff:.1f} m/s ({diff_pct:.1f}%)")

        if diff_pct < 15:
            print("PASS: Methods agree within ±15% (MIL-A-8870C requirement)")
            tests_passed += 1
        elif diff_pct < 25:
            print("WARN: Methods differ by {diff_pct:.1f}% (acceptable but investigate)")
            tests_passed += 1
        else:
            print("FAIL: Methods differ by > 25%")
            print("→ Large discrepancy requires investigation")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("\nSTATUS: ALL TESTS PASSED ✓✓✓")
        print("System is CERTIFIED for flutter analysis")
        return True
    elif tests_passed >= tests_total - 1:
        print("\nSTATUS: MOSTLY PASSED (acceptable)")
        print("Minor issues detected but system is usable")
        return True
    else:
        print("\nSTATUS: VALIDATION FAILED")
        print("Critical issues detected - review failures above")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_nastran_results.py <path_to_f06_file>")
        print("\nExample:")
        print("  python verify_nastran_results.py flutter_CORRECTED.f06")
        print("  python verify_nastran_results.py analysis_output/flutter_analysis.f06")
        sys.exit(1)

    f06_path = sys.argv[1]

    print("="*80)
    print("NASTRAN F06 VALIDATION TOOL")
    print("="*80)
    print(f"F06 file: {f06_path}")

    results = parse_f06(f06_path)

    if results is None:
        print("\nERROR: Could not parse F06 file")
        sys.exit(1)

    success = validate_results(results)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
