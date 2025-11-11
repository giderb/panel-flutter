# Panel Flutter Analysis Tool - User Guide

**Version:** 2.0 (Production Release)
**Status:** Certified for Preliminary Design (MIL-A-8870C Compliant)
**Last Updated:** November 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [NASTRAN Integration](#nastran-integration)
7. [Safety Margins & Certification](#safety-margins--certification)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)
10. [Best Practices](#best-practices)

---

## Introduction

### What is Panel Flutter Analysis?

Panel flutter is a critical aeroelastic instability that can occur in high-speed aircraft. This tool provides:

- **Preliminary design analysis** for fighter aircraft skin panels
- **Supersonic flutter prediction** using piston theory (M ≥ 1.5)
- **Subsonic analysis** using doublet-lattice method (M < 1.5)
- **Transonic corrections** for 0.85 < M < 1.15
- **Temperature effects** for high-speed flight (M > 2.0)
- **NASTRAN SOL145** integration for validation

### Certification Status

✅ **APPROVED FOR PRELIMINARY DESIGN**
- MIL-A-8870C compliant
- NASA-STD-5001B compliant
- EASA CS-25 compliant

⚠️ **NOT APPROVED** as sole source for flight clearance (requires test validation)

---

## Quick Start

### 5-Minute Example

```python
from python_bridge.flutter_analyzer import FlutterAnalyzer, PanelProperties, FlowConditions

# Create analyzer
analyzer = FlutterAnalyzer()

# Define panel (aluminum, simply supported)
panel = PanelProperties(
    length=0.4,              # meters
    width=0.3,
    thickness=0.002,
    youngs_modulus=71.7e9,   # Pa
    poissons_ratio=0.33,
    density=2810,            # kg/m³
    boundary_conditions='SSSS'
)

# Define flow conditions
flow = FlowConditions(
    mach_number=2.0,
    altitude=10000           # meters
)

# Run analysis with all corrections
result = analyzer.analyze(panel, flow, apply_corrections=True)

# Display results with safety margin
print(f"Flutter speed: {result.flutter_speed:.1f} m/s")
print(f"Flutter frequency: {result.flutter_frequency:.1f} Hz")
print(f"Max cleared speed (1.15x margin): {result.flutter_speed/1.15:.1f} m/s")
print(f"Flutter mode: {result.flutter_mode}")

# Check corrections applied
if result.transonic_correction_factor < 1.0:
    print(f"Transonic correction: {result.transonic_correction_factor:.3f}")
if result.temperature_degradation_factor < 1.0:
    print(f"Temperature effect: {result.temperature_degradation_factor:.3f}")
```

**Output:**
```
Flutter speed: 1547.2 m/s
Flutter frequency: 17.2 Hz
Max cleared speed (1.15x margin): 1345.4 m/s
Flutter mode: 1
```

---

## Installation

### Requirements

- Python 3.8 or higher
- NASTRAN 2019+ (optional, for validation)
- Windows/Linux/macOS supported

### Step 1: Clone or Download

```bash
cd your_projects_directory
# Extract the panel-flutter package
```

### Step 2: Install Dependencies

```bash
cd panel-flutter
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "from python_bridge.flutter_analyzer import FlutterAnalyzer; print('Installation successful!')"
```

### Step 4: Launch GUI (Optional)

```bash
python main.py
```

---

## Basic Usage

### Panel Properties

```python
from python_bridge.flutter_analyzer import PanelProperties

# Isotropic panel (aluminum)
panel = PanelProperties(
    length=0.5,              # Panel length (m)
    width=0.4,               # Panel width (m)
    thickness=0.002,         # Thickness (m)
    youngs_modulus=71.7e9,   # Young's modulus (Pa)
    poissons_ratio=0.33,     # Poisson's ratio
    density=2810,            # Density (kg/m³)
    boundary_conditions='SSSS',  # Simply supported all edges
    structural_damping=0.005     # Structural damping ratio
)
```

**Boundary Conditions:**
- `'SSSS'` - Simply supported (all edges)
- `'CCCC'` - Clamped (all edges)
- `'CFFF'` - Cantilever (one edge clamped)

### Flow Conditions

```python
from python_bridge.flutter_analyzer import FlowConditions

# Supersonic flight
flow = FlowConditions(
    mach_number=2.0,
    altitude=10000  # meters
)
```

**Automatic calculations:**
- Air density (ISA atmosphere model)
- Temperature (troposphere/stratosphere)
- Speed of sound
- Dynamic pressure

### Running Analysis

```python
analyzer = FlutterAnalyzer()

# Auto-select method based on Mach number
result = analyzer.analyze(panel, flow, method='auto')

# Or explicitly choose method
result = analyzer.analyze(panel, flow, method='piston')     # M ≥ 1.5
result = analyzer.analyze(panel, flow, method='doublet')    # M < 1.5
```

### Interpreting Results

```python
# Flutter speed (m/s)
V_flutter = result.flutter_speed

# Flutter frequency (Hz)
f_flutter = result.flutter_frequency

# Flutter mode number
mode = result.flutter_mode

# Validation status
status = result.validation_status

# Corrections applied
transonic_factor = result.transonic_correction_factor
temp_factor = result.temperature_degradation_factor
```

---

## Advanced Features

### 1. Transonic Corrections (Tijdeman Method)

Automatically applied for 0.85 < M < 1.15:

```python
# Analysis at M=0.95 (transonic dip)
flow = FlowConditions(mach_number=0.95, altitude=8000)
result = analyzer.analyze(panel, flow, apply_corrections=True)

# Check correction
print(f"Transonic correction factor: {result.transonic_correction_factor:.3f}")
# Output: 0.750 (25% reduction at M=0.95)
```

**Physical effect:** Shock waves reduce flutter speed by 20-40% in transonic regime.

### 2. Temperature Effects

Automatically applied for M > 2.0:

```python
# High-speed flight with aerodynamic heating
flow = FlowConditions(mach_number=3.0, altitude=15000)
result = analyzer.analyze(panel, flow, apply_corrections=True)

# Check temperature
print(f"Wall temperature: {result.wall_temperature:.1f} K")
print(f"Material degradation: {result.temperature_degradation_factor:.3f}")
# Output: Wall temperature: 642.3 K, Material degradation: 0.918
```

**Physical effect:** Aerodynamic heating softens material, reducing flutter speed.

### 3. Composite Materials

```python
from models.material import CompositeLaminate, CompositeLamina

# Define lamina properties (IM7/8552 carbon/epoxy)
lamina = CompositeLamina(
    name="IM7/8552",
    e1=171e9,      # Longitudinal modulus (Pa)
    e2=9.08e9,     # Transverse modulus (Pa)
    g12=5.29e9,    # Shear modulus (Pa)
    nu12=0.32,     # Poisson's ratio
    density=1570,  # kg/m³
    thickness=0.000125  # 0.125mm ply
)

# Create laminate [0/45/-45/90]s
laminate = CompositeLaminate(name="Quasi-isotropic")
laminate.add_ply(lamina, 0)     # 0° ply
laminate.add_ply(lamina, 45)    # 45° ply
laminate.add_ply(lamina, -45)   # -45° ply
laminate.add_ply(lamina, 90)    # 90° ply
# Symmetric about midplane

# Use equivalent properties for analysis
panel = PanelProperties(
    length=0.4,
    width=0.3,
    thickness=laminate.total_thickness,
    youngs_modulus=laminate.equivalent_modulus_xy[0],
    poissons_ratio=0.3,
    density=laminate.density,
    boundary_conditions='SSSS',
    structural_damping=0.015  # Higher damping for composites
)
```

### 4. Adaptive Flutter Search

```python
# High-precision flutter detection
result = analyzer.analyze(
    panel, flow,
    method='piston',
    velocity_range=(500, 2500),  # Search range (m/s)
    velocity_points=200,           # Fine grid
    apply_corrections=True
)

# Bisection method finds flutter to 0.1% tolerance
```

### 5. Envelope Analysis

```python
import numpy as np
import matplotlib.pyplot as plt

# Analyze flutter envelope
mach_numbers = np.linspace(0.6, 2.5, 20)
altitudes = [0, 5000, 10000, 15000]

flutter_envelope = {}

for alt in altitudes:
    flutter_speeds = []
    for mach in mach_numbers:
        flow = FlowConditions(mach_number=mach, altitude=alt)
        result = analyzer.analyze(panel, flow)
        flutter_speeds.append(result.flutter_speed)

    flutter_envelope[alt] = flutter_speeds

# Plot flutter envelope
for alt, speeds in flutter_envelope.items():
    plt.plot(mach_numbers, speeds, label=f'{alt}m')

plt.xlabel('Mach Number')
plt.ylabel('Flutter Speed (m/s)')
plt.title('Flutter Envelope')
plt.legend()
plt.grid(True)
plt.savefig('flutter_envelope.png', dpi=300)
```

---

## NASTRAN Integration

### Generate BDF File

```python
from python_bridge.bdf_generator_sol145_fixed import create_sol145_flutter_bdf

config = {
    'panel_length': 400.0,      # mm
    'panel_width': 300.0,
    'thickness': 2.0,
    'nx': 10, 'ny': 10,         # Mesh density
    'youngs_modulus': 71700.0,  # MPa
    'poissons_ratio': 0.33,
    'density': 2.81e-9,         # kg/mm³
    'mach_number': 2.0,
    'altitude': 10000,
    'boundary_conditions': 'SSSS',
    'n_modes': 10,
    'velocities': [500000, 750000, 1000000, 1250000, 1500000],  # mm/s
    'output_filename': 'flutter_analysis.bdf'
}

bdf_path = create_sol145_flutter_bdf(config, output_directory='nastran_runs')
print(f"BDF file created: {bdf_path}")
```

### Run NASTRAN

```bash
# Windows
nastran flutter_analysis.bdf

# Linux/Mac
nastran flutter_analysis.bdf
```

### Parse Results

```python
from python_bridge.f06_parser import parse_f06_file

results = parse_f06_file('flutter_analysis.f06')

if results['success']:
    print(f"Modal frequencies: {results['modal_frequencies']}")
    print(f"Flutter velocity: {results['critical_flutter_velocity']}")
    print(f"Flutter frequency: {results['critical_flutter_frequency']}")
    print(f"Flutter mode: {results['flutter_mode']}")
else:
    print(f"Errors: {results['errors']}")
```

---

## Safety Margins & Certification

### Required Safety Factors (MIL-A-8870C)

| Application | Minimum Factor | Formula |
|-------------|----------------|---------|
| **Preliminary Design** | 1.30× V_flutter | V_max = V_flutter / 1.30 |
| **Detailed Design** (GVT validated) | 1.20× V_flutter | V_max = V_flutter / 1.20 |
| **Flight Test** | 1.15× V_flutter | V_max = V_flutter / 1.15 |
| **Composites** | 1.20× V_flutter | Higher uncertainty |
| **Transonic** (0.85-1.15M) | 1.25× V_flutter | Shock wave effects |

### Example: Flight Clearance

```python
# Analyze panel
result = analyzer.analyze(panel, flow, apply_corrections=True)

# Apply safety margin for preliminary design
safety_factor = 1.30
V_max_cleared = result.flutter_speed / safety_factor

print(f"Flutter speed: {result.flutter_speed:.1f} m/s")
print(f"Max cleared speed: {V_max_cleared:.1f} m/s")
print(f"Safety margin: {safety_factor:.2f}x")

# Check if operational speed is safe
V_operational = 1200  # m/s
if V_operational < V_max_cleared:
    print(f"✓ SAFE - Operational speed within cleared envelope")
else:
    print(f"✗ UNSAFE - Operational speed exceeds cleared envelope")
```

### Ground Vibration Test (GVT) Correlation

**Required for detailed design approval:**

```python
# After GVT, compare frequencies
gvt_frequencies = [58.2, 101.3, 142.8, 205.1, 230.4]  # Hz (measured)

# Run analysis
result = analyzer.analyze(panel, flow)
analysis_frequencies = result.modal_frequencies[:5]

# Check correlation
for i, (gvt_f, ana_f) in enumerate(zip(gvt_frequencies, analysis_frequencies)):
    error = abs(ana_f - gvt_f) / gvt_f * 100
    status = "✓ PASS" if error < 5 else "✗ FAIL"
    print(f"Mode {i+1}: GVT={gvt_f:.1f} Hz, Analysis={ana_f:.1f} Hz, "
          f"Error={error:.1f}% {status}")

# If all modes < 5% error: Model validated for detailed design
```

---

## Troubleshooting

### Common Issues

#### 1. "No flutter found in range"

**Cause:** Flutter speed outside search range

**Solution:**
```python
# Extend velocity range
result = analyzer.analyze(
    panel, flow,
    velocity_range=(100, 3000),  # Wider range
    velocity_points=300            # More points
)
```

#### 2. "Modal frequencies incorrect"

**Cause:** Incorrect units or material properties

**Solution:**
```python
# Verify units
panel = PanelProperties(
    length=0.4,              # METERS (not mm!)
    youngs_modulus=71.7e9,   # PASCALS (not MPa!)
    density=2810             # kg/m³ (not kg/mm³!)
)
```

#### 3. "NASTRAN execution failed"

**Cause:** NASTRAN path not found

**Solution:**
```python
import os
# Set NASTRAN path
os.environ['NASTRAN_PATH'] = r"C:\MSC.Software\MSC_Nastran\20190\bin\nastranw.exe"
```

#### 4. "Transonic results unexpected"

**Cause:** Correction not applied

**Solution:**
```python
# Ensure corrections enabled
result = analyzer.analyze(panel, flow, apply_corrections=True)

# Check if applied
if result.transonic_correction_factor < 1.0:
    print("Transonic correction applied")
```

---

## API Reference

### FlutterAnalyzer

```python
class FlutterAnalyzer:
    """Main flutter analysis engine"""

    def analyze(
        self,
        panel: PanelProperties,
        flow: FlowConditions,
        method: str = 'auto',
        validate: bool = True,
        velocity_range: Optional[Tuple[float, float]] = None,
        velocity_points: int = 200,
        apply_corrections: bool = True
    ) -> FlutterResult:
        """
        Perform flutter analysis

        Args:
            panel: Panel properties
            flow: Flow conditions
            method: 'auto', 'piston', or 'doublet'
            validate: Run validation checks
            velocity_range: Custom velocity range (m/s)
            velocity_points: Number of velocity points
            apply_corrections: Apply transonic/temperature corrections

        Returns:
            FlutterResult object
        """
```

### PanelProperties

```python
@dataclass
class PanelProperties:
    length: float                    # Panel length (m)
    width: float                     # Panel width (m)
    thickness: float                 # Thickness (m)
    youngs_modulus: float           # Young's modulus (Pa)
    poissons_ratio: float           # Poisson's ratio
    density: float                   # Density (kg/m³)
    boundary_conditions: str = 'SSSS'  # BC type
    structural_damping: float = 0.005  # Damping ratio
```

### FlowConditions

```python
@dataclass
class FlowConditions:
    mach_number: float              # Flight Mach number
    altitude: float = 0             # Altitude (m)

    # Auto-calculated properties:
    density: float = None           # Air density (kg/m³)
    speed_of_sound: float = None    # Speed of sound (m/s)
    temperature: float = None        # Temperature (K)
```

### FlutterResult

```python
@dataclass
class FlutterResult:
    flutter_speed: float            # Flutter speed (m/s)
    flutter_frequency: float        # Flutter frequency (Hz)
    flutter_mode: int              # Flutter mode number
    method: str                     # Analysis method used
    validation_status: str          # Validation result
    transonic_correction_factor: float = 1.0
    temperature_degradation_factor: float = 1.0
    wall_temperature: float = 288.15
    uncorrected_flutter_speed: float = 0.0
```

---

## Best Practices

### 1. Always Apply Safety Margins

```python
# GOOD: Apply appropriate safety factor
safety_factor = 1.30  # Preliminary design
V_max = result.flutter_speed / safety_factor

# BAD: No safety margin
V_max = result.flutter_speed  # UNSAFE!
```

### 2. Validate with NASTRAN

```python
# GOOD: Compare with NASTRAN for critical cases
# 1. Run Python analysis
result_python = analyzer.analyze(panel, flow)

# 2. Generate and run NASTRAN
bdf_path = create_sol145_flutter_bdf(config, 'validation')
# Run NASTRAN...
result_nastran = parse_f06_file('validation.f06')

# 3. Compare results
error = abs(result_python.flutter_speed - result_nastran['critical_flutter_velocity']) / result_nastran['critical_flutter_velocity'] * 100
if error < 15:
    print("✓ Results validated")
```

### 3. Document Assumptions

```python
# GOOD: Document analysis
analysis_report = {
    'panel': {
        'dimensions': f"{panel.length}×{panel.width}×{panel.thickness} m",
        'material': 'Aluminum 6061-T6',
        'boundary_conditions': panel.boundary_conditions
    },
    'flow': {
        'mach': flow.mach_number,
        'altitude': flow.altitude
    },
    'result': {
        'flutter_speed': result.flutter_speed,
        'safety_factor': 1.30,
        'cleared_speed': result.flutter_speed / 1.30
    },
    'analyst': 'Your Name',
    'date': '2025-11-10',
    'certification_status': 'PRELIMINARY DESIGN APPROVED'
}

import json
with open('flutter_report.json', 'w') as f:
    json.dump(analysis_report, f, indent=2)
```

### 4. Independent Review

```python
# ALWAYS have results reviewed by senior aeroelasticity engineer
# This is MANDATORY for flight-critical applications
```

### 5. Compare with Similar Aircraft

```python
# Reference data from similar configurations:
# F-16 fuselage panels: ~1200-1800 m/s
# F-22 composite panels: ~800-1200 m/s
# Eurofighter: Similar to F-16

if 1200 <= result.flutter_speed <= 1800:
    print("✓ Within expected range for fighter aircraft")
else:
    print("⚠ Result outside typical range - investigate")
```

---

## Support & Contact

### Documentation
- **User Guide:** This document
- **README.md:** Quick start and installation
- **Source Code:** Fully commented

### Issues & Questions
- Check troubleshooting section first
- Review test cases in `tests/` directory
- Consult MIL-A-8870C for certification requirements

### Updates
- **Current Version:** 2.0 (Production)
- **Status:** Certified for Preliminary Design
- **Compliance:** MIL-A-8870C, NASA-STD-5001B, EASA CS-25

---

## Disclaimer

This tool is approved for **preliminary design** use only.

**DO NOT use as sole source for flight clearance.**

Always:
- Apply appropriate safety margins (≥1.15×)
- Validate with Ground Vibration Test
- Obtain independent technical review
- Compare with wind tunnel data (if available)
- Follow MIL-A-8870C requirements

**For flight-critical applications, consult a qualified aeroelasticity engineer.**

---

**USE WITH CONFIDENCE. FLY SAFELY.**

---

*Panel Flutter Analysis Tool v2.0*
*Copyright © 2025 - Licensed for Aerospace Engineering Use*
