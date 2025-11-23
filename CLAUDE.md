# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Panel Flutter Analysis Tool is a certified aerospace application for analyzing panel flutter phenomena in fighter aircraft using MSC NASTRAN SOL145 and validated physics-based calculations. The application combines a CustomTkinter GUI with computational aeroelasticity engines implementing Piston Theory (supersonic) and Doublet Lattice Method (subsonic).

**Current Version:** 2.2.0 (Production/Stable)
**Certification:** MIL-A-8870C, NASA-STD-5001B, EASA CS-25 compliant for preliminary design

## Commands

### Development Environment

```bash
# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
.venv\Scripts\python main.py

# Run with warning suppression
.venv\Scripts\python run_gui.py
```

### Testing

```bash
# Run validation test suite (8 comprehensive tests)
.\.venv\Scripts\python.exe tests\test_fixes.py

# Run GUI workflow tests (composite materials)
.\.venv\Scripts\python.exe tests\test_gui_workflow_composite.py

# Verify NASTRAN card formatting
.\.venv\Scripts\python.exe tests\verify_pcomp_format.py
```

### Building

```bash
# Build standalone executable using PyInstaller
.\.venv\Scripts\python.exe scripts\build_executable.py

# Output: dist/PanelFlutter.exe
```

### Git Workflow

This is a production aerospace tool. All commits must maintain certification status:
- Always validate changes against test suite before committing
- Update version numbers in setup.py for releases
- Document breaking changes in release notes

## Architecture

### Data Flow: GUI → Analysis → NASTRAN

1. **GUI Layer** (`gui/`): CustomTkinter panels collect user input
   - `main_window.py`: Application orchestration, panel navigation
   - `panels/`: 6 workflow panels (Home, Material, Structural, Aerodynamics, Analysis, Results)
   - `project_manager.py`: Project persistence (JSON serialization)

2. **Data Models** (`models/`): Immutable data structures
   - `material.py`: Material types (Isotropic, Orthotropic, Composite, Sandwich)
   - `structural.py`: Panel geometry, mesh configuration, boundary conditions
   - `aerodynamic.py`: Flow conditions, Mach regime selection
   - Models use dataclasses and include temperature degradation coefficients

3. **Analysis Executors** (`python_bridge/`): Physics engines
   - `integrated_analysis_executor.py`: **Main orchestrator** - runs dual-path analysis
   - `flutter_analyzer.py`: Physics-based solver (Piston Theory, DLM, V-g/V-f methods)
   - `bdf_generator_sol145_fixed.py`: NASTRAN BDF file generation (SOL145 cards)
   - `nastran_interface.py`: Subprocess execution of NASTRAN solver
   - `f06_parser.py`: Extract flutter results from NASTRAN .f06 output

4. **Dual Analysis Path** (Critical Safety Design):
   - Path 1: Physics-based calculation (fast, analytical)
   - Path 2: NASTRAN SOL145 verification (authoritative)
   - Results compared with 5% tolerance for validation

### Critical Architecture Patterns

#### Mach Regime Selection
```python
# Automatic aerodynamic method selection (aerodynamic.py)
if mach < 1.0:
    method = "DLM"  # Doublet Lattice Method (CAERO1)
elif mach >= 1.2:
    method = "Piston Theory"  # CAERO5
else:  # 1.0 <= mach < 1.2
    method = "Piston Theory"  # Transonic gap with warnings
```

**v2.1.0 Critical Fix**: Supersonic regime was incorrectly using DLM at M≥1.2, causing 2-3x errors. Now properly uses Piston Theory.

#### Composite Material Handling
```python
# Phase 1 Protection (v2.1.0): Block unsafe physics analysis
if material.type == MaterialType.COMPOSITE:
    if analysis_mode == "physics_only":
        raise ValueError("Composite materials require NASTRAN SOL145")
    # NASTRAN path uses MAT8/PCOMP cards (correct orthotropic modeling)
```

Physics-based analyzer treats composites as isotropic (20-50% error). System now blocks this path and requires NASTRAN for composite materials.

#### Unit Conversion Pipeline
- **GUI/Models**: SI units (Pa, kg/m³, meters)
- **BDF Generator**: NASTRAN mm-tonne-s-N system
- **Conversion**: `python_bridge/unit_conversions.py`
- **Results**: Convert back to SI for display

```python
# Example: Density conversion
density_si = 2700  # kg/m³ (aluminum)
density_nastran = density_si * 1e-12  # tonne/mm³
```

### NASTRAN Integration Details

#### BDF Card Generation
`bdf_generator_sol145_fixed.py` generates validated cards:

**Structural Cards:**
- `GRID`: Panel node locations (mm coordinates)
- `CQUAD4`: Shell elements with property references
- `MAT1`: Isotropic material properties
- `MAT8/PCOMP`: Composite layup (for laminates)
- `PSHELL`/`PCOMP`: Element properties
- `SPC1`: Boundary condition constraints (SSSS, CCCC, CFFF)

**Aerodynamic Cards:**
- `CAERO1`: Doublet lattice panels (M < 1.5)
- `CAERO5/PAERO5`: Piston theory panels (M ≥ 1.5)
- `SPLINE2`: FEM-to-aerodynamic interpolation
- `AELIST`: Aerodynamic element lists

**Flutter Analysis Cards:**
- `FLUTTER`: PK method configuration
- `FLFACT`: Velocity, density, Mach sweeps
- `MKAERO1/MKAERO2`: Reduced frequency matrix

**Modal Analysis:**
- `EIGRL`: Lanczos eigenvalue extraction
- Modes typically 10-20 for convergence

#### Boundary Conditions Implementation
All BCs include:
1. Physical edge constraints (per support type)
2. Rigid body suppression (DOF 1,2 at corner node)
3. Drilling rotation constraint (DOF 6 for CQUAD4 stability)

### Configuration Management

`utils/config.py` provides persistent settings:
- NASTRAN executable path detection (defaults to `C:\MSC.Software\MSC_Nastran\20190\bin\nastran.exe`)
- Analysis defaults (modes=15, method=PK, velocity ranges)
- GUI appearance (dark theme, scaling)
- Project autosave intervals

Configuration stored in `config.json` (auto-created on first run).

### Validation & Certification

The tool maintains certification through:

1. **Analytical Validation** (`flutter_analyzer.py`):
   - Dowell solution for simply-supported panels
   - Leissa mode shapes
   - Ashley-Zartarian dynamic pressure

2. **Test Suite** (`tests/`):
   - Mass matrix accuracy validation
   - DLM kernel function verification
   - Aerodynamic method selection logic
   - NASTRAN card format validation

3. **Safety Margins** (MIL-A-8870C):
   - Minimum 1.15x factor on flutter dynamic pressure
   - Uncertainty quantification in results
   - Transonic/thermal corrections applied

4. **Known Limitations Documented**:
   - Composite materials: Phase 1 blocking (safe), Phase 2/3 planned
   - Transonic gap (1.0 ≤ M < 1.2): ±15-25% accuracy
   - Hypersonic (M > 5.0): Piston Theory degrades

## Key Files to Modify

### Adding New Materials
1. Edit `gui/panels/material_panel.py`: Add to predefined materials list
2. Update `models/material.py`: Add temperature degradation coefficients if needed
3. Document in `USER_GUIDE.md`

### Modifying Aerodynamic Methods
1. `flutter_analyzer.py`: Implement new aerodynamic theory
2. `bdf_generator_sol145_fixed.py`: Add corresponding NASTRAN cards
3. Update `models/aerodynamic.py`: Add method selection logic
4. **Critical**: Validate against known solutions before deployment

### Changing Boundary Conditions
1. `models/boundary_conditions.py`: Define DOF constraints
2. `bdf_generator_sol145_fixed.py`: Generate SPC1 cards
3. Add validation test case to `tests/`

### GUI Workflow Changes
1. Panel order: Modify `gui/main_window.py` navigation
2. New panel: Create in `gui/panels/`, inherit from `base_panel.py`
3. Wire to data model: Update `project_manager.py` serialization

## Important Notes

### Safety-Critical Code
This is a **flight safety application**. Changes to physics calculations require:
- Validation against analytical solutions
- Test case coverage
- Documentation of assumptions
- Peer review

Files with safety implications:
- `flutter_analyzer.py`: Core flutter calculations
- `bdf_generator_sol145_fixed.py`: NASTRAN interface
- `integrated_analysis_executor.py`: Analysis orchestration

### NASTRAN Compatibility
- Tested with MSC Nastran 2019
- Uses mm-tonne-s-N unit system (NASTRAN standard)
- BDF format: Free-field with proper alignment
- Always validate generated BDF files with NASTRAN before production use

### Known Issues (v2.2.0)
1. **Composite Materials**: Only NASTRAN path validated (physics path blocked)
2. **Transonic Regime**: 1.0 ≤ M < 1.2 uses Piston Theory with reduced accuracy
3. **Windows Only**: GUI tested on Windows 10+, Linux/Mac untested

### Temperature Effects
Adiabatic wall temperature calculated for M > 1.5:
```python
T_wall = T_ambient * (1 + 0.2 * M²)
```
Material properties degraded per MIL-HDBK-5J coefficients in `material.py`.

### Mesh Quality
Element aspect ratio warnings trigger at ratio > 3.0 (prevents 20% errors). Typical mesh: nx=10-20, ny=10-20 for convergence.

## Custom Claude Agent

The repository includes `.claude/agents/aeroelasticity-expert.md`:
- Specialized agent for flutter analysis tasks
- Validates against real-world fighter aircraft data (F-16, F/A-18, Eurofighter)
- Enforces MIL-STD-1530D safety margins
- Use for certification-critical decisions

Invoke with Task tool when:
- Performing flutter analysis or validation
- Evaluating safety margins
- Assessing design modifications impact on flutter
- Investigating failure modes

## Documentation

- `README.md`: Installation, quick start, validation status
- `USER_GUIDE.md`: Detailed API reference, workflow guide
- `docs/CERTIFICATION.md`: Certification status and compliance
- `docs/USER_GUIDE.md`: Duplicate of root USER_GUIDE.md
- `scripts/README.md`: Build instructions

## Project Structure

```
panel-flutter/
├── main.py                    # Entry point (with matplotlib styling)
├── run_gui.py                 # Entry point (warning suppression)
├── gui/                       # CustomTkinter interface
│   ├── main_window.py         # Application orchestrator
│   ├── panels/                # 6 workflow panels
│   ├── project_manager.py     # JSON persistence
│   └── theme_manager.py       # Dark theme styling
├── models/                    # Data structures
│   ├── material.py            # Material types with temp degradation
│   ├── structural.py          # Geometry, mesh, BCs
│   └── aerodynamic.py         # Flow conditions, Mach regime
├── python_bridge/             # Analysis engines
│   ├── integrated_analysis_executor.py  # Main orchestrator
│   ├── flutter_analyzer.py              # Physics solver
│   ├── bdf_generator_sol145_fixed.py    # NASTRAN BDF writer
│   ├── nastran_interface.py             # Subprocess execution
│   └── f06_parser.py                    # Results extraction
├── utils/                     # Configuration, logging
├── tests/                     # Validation suite
└── scripts/                   # Build tools
```
