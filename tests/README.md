# Tests

This folder contains all test files for the Panel Flutter Analysis application.

## Test Files

### Validation Tests

- **`test_fixes.py`** - Comprehensive validation of all critical fixes
  - Tests element aspect ratio validation
  - Validates improved mass matrix
  - Checks configurable structural damping
  - Verifies Doublet-Lattice Method implementation
  - Tests aerodynamic method auto-selection

  **Run with:**
  ```bash
  .\.venv\Scripts\python.exe tests\test_fixes.py
  ```

### GUI Workflow Tests

- **`test_gui_workflow_composite.py`** - GUI workflow test for composite materials
  - Tests complete analysis workflow
  - Validates composite material handling
  - Checks GUI state management

### Verification Scripts

- **`verify_pcomp_format.py`** - NASTRAN PCOMP card format verification
  - Validates BDF file generation
  - Checks composite laminate card format
  - Ensures NASTRAN compatibility

## Running All Tests

From the project root:

```bash
# Run critical fixes validation
.\.venv\Scripts\python.exe tests\test_fixes.py

# Run GUI workflow test (requires GUI environment)
.\.venv\Scripts\python.exe tests\test_gui_workflow_composite.py

# Run PCOMP verification
.\.venv\Scripts\python.exe tests\verify_pcomp_format.py
```

## Test Coverage

Current test coverage:
- ✅ Backend calculations (mass matrix, damping, DLM)
- ✅ Input validation (all GUI parameters)
- ✅ Aerodynamic method selection
- ✅ Element quality checks
- ✅ NASTRAN BDF generation
- ⚠️ Full integration tests (manual testing required)

## Expected Results

All automated tests should pass with output similar to:
```
======================================================================
VALIDATION COMPLETE - ALL CRITICAL FIXES VERIFIED
======================================================================

Summary of fixes:
  + Element aspect ratio validation with warnings
  + Improved mass matrix formulation (5-15% better accuracy)
  + Configurable structural damping parameter
  + GUI input range validation for all physical parameters
  + Full Doublet-Lattice Method with Albano-Rodden kernel functions
  + Enhanced aerodynamic method selection (DLM for M<1.5, Piston for M>=1.5)
```

## Adding New Tests

When adding new tests:
1. Follow the naming convention: `test_*.py`
2. Include clear test descriptions
3. Use assertions for validation
4. Add expected outputs to this README
5. Update the test coverage section

## Continuous Integration

These tests are designed to be run:
- Before committing changes
- After major refactoring
- Before releases
- As part of CI/CD pipelines

---

*Last Updated: 2025-11-02*
