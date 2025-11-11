# NASTRAN SOL145 FLUTTER ANALYSIS - VALIDATION CHECKLIST

**Purpose:** Ensure flutter analysis meets aerospace certification standards
**Scope:** Pre-run and post-run validation for critical safety analyses
**Authority:** MIL-A-8870C, FAA AC 25.629-1B, EASA CS-25.629

---

## PRE-RUN VALIDATION CHECKLIST

**File:** `______________________________.bdf`
**Analyst:** `______________________________`
**Date:** `______________________________`
**Review:** ☐ Self-Check ☐ Peer Review

### 1. Executive Control Section

```bash
grep -A 5 "^SOL" your_file.bdf
```

- [ ] **SOL 145** specified (flutter analysis)
- [ ] **CEND** present (end of executive control)

### 2. Case Control Section

```bash
sed -n '/CEND/,/BEGIN BULK/p' your_file.bdf
```

- [ ] **TITLE** present (descriptive)
- [ ] **SPC = 1** (boundary conditions referenced)
- [ ] **METHOD = 1** (eigenvalue extraction referenced)
- [ ] **FMETHOD = 1** (flutter method referenced)
- [ ] **BEGIN BULK** present

### 3. Critical Flutter Parameters

```bash
grep "PARAM.*KDAMP" your_file.bdf
grep "TABDMP1" your_file.bdf
```

- [ ] **PARAM KDAMP** present with table ID (e.g., KDAMP 1)
- [ ] **TABDMP1** card present with matching ID
- [ ] **Damping values** reasonable (0.01-0.05 for aerospace structures)
- [ ] **Frequency range** covers expected modes (0.0 to 1000+ Hz)
- [ ] **ENDT** terminator present

**Example:**
```nastran
PARAM   KDAMP   1
TABDMP1 1       CRIT
+       0.0     0.03    1000.0  0.03    ENDT
```

### 4. Flutter Analysis Cards

```bash
grep "FLUTTER" your_file.bdf
grep "FLFACT" your_file.bdf
```

- [ ] **FLUTTER** card present (PK method recommended)
- [ ] **FLFACT 1** density ratio (typically 0.5 for one-sided flow)
- [ ] **FLFACT 2** Mach number(s) (match flight condition)
- [ ] **FLFACT 3** velocities or reduced frequencies
  - [ ] Range includes expected flutter speed
  - [ ] Extends ≥15% beyond predicted flutter (MIL-A-8870C)
  - [ ] Sufficient resolution (≥10 points)

**Example:**
```nastran
FLUTTER 1       PK      1       2       3       L
FLFACT  1       0.5
FLFACT  2       0.8
FLFACT  3       1.0E+05 2.0E+05 3.0E+05 ... 2.5E+06
```

### 5. Aerodynamic Model

```bash
grep "MKAERO1" your_file.bdf
grep "CAERO" your_file.bdf
grep "PAERO" your_file.bdf
```

#### For Doublet-Lattice Method (M < 1.5):

- [ ] **CAERO1** panel defined
- [ ] **PAERO1** property card present
- [ ] **MKAERO1** with Mach number matching FLFACT 2
- [ ] **Reduced frequencies** include low values (0.001, 0.01, 0.1, ...)
  - [ ] **CRITICAL:** Leading zeros present (0.001 not .001)
- [ ] **Panel mesh** adequate (≥8×8 for panels, ≥20 spanwise for wings)

**Example:**
```nastran
MKAERO1 0.8                                                             +MK1
+MK1    0.001   0.01    0.1     0.2     0.4
```

#### For Piston Theory (M ≥ 1.5):

- [ ] **CAERO5** panel defined
- [ ] **PAERO5** property card with continuation lines
- [ ] **AEFACT** thickness integrals (zeros for flat panels)
- [ ] **MKAERO1** (NOT MKAERO2) with supersonic Mach numbers
- [ ] **PARAM OPPHIPA 1** for higher-order piston theory

### 6. Structural Model

```bash
grep "MAT1\|MAT8" your_file.bdf
grep "PSHELL\|PCOMP" your_file.bdf
grep "EIGRL\|EIGR" your_file.bdf
```

- [ ] **Material cards** present (MAT1 or MAT8)
  - [ ] Young's modulus reasonable (e.g., 71.7 GPa for Al)
  - [ ] Density correct units (kg/mm³ for mm-kg-s-N system)
- [ ] **Property cards** present (PSHELL or PCOMP)
  - [ ] Thickness correct
- [ ] **Eigenvalue extraction** (EIGRL or EIGR)
  - [ ] Sufficient modes requested (≥2× flutter modes expected)
  - [ ] Frequency range appropriate

### 7. Boundary Conditions

```bash
grep "SPC1" your_file.bdf
```

- [ ] **SPC1** cards define boundary conditions correctly
  - [ ] SSSS: DOF 3 (Z) on all edges
  - [ ] CCCC: DOF 123456 on all edges
  - [ ] CFFF: DOF 123456 on one edge only
- [ ] **Rigid body constraints** prevent singularities
  - [ ] DOF 1 (X) at one corner
  - [ ] DOF 2 (Y) at two corners
  - [ ] DOF 6 (drilling rotation) on ALL nodes for CQUAD4

### 8. Spline Interpolation

```bash
grep "SPLINE1\|SPLINE2" your_file.bdf
grep "SET1" your_file.bdf
```

- [ ] **SPLINE1 or SPLINE2** connects aero to structure
- [ ] **CAERO** box range correct (BOX1 to BOX2)
- [ ] **SET1** includes all structural grids
- [ ] **DZ offset** appropriate (typically 0.0 for panels)

### 9. Unit Consistency

**System:** ☐ mm-kg-s-N ☐ m-kg-s-N ☐ in-lbf-s ☐ Other: _______

- [ ] **Length units** consistent (grids, chord, thickness)
- [ ] **Density units** correct:
  - [ ] Structural: kg/mm³ = kg/m³ × 1e-9 (for mm system)
  - [ ] Air: kg/mm³ = kg/m³ × 1e-9 (for mm system)
- [ ] **Modulus units** correct:
  - [ ] MPa = N/mm² for mm system
- [ ] **Velocity units** match AERO VREF:
  - [ ] mm/s for mm system
  - [ ] m/s for m system

### 10. Comments and Documentation

- [ ] **Header comments** describe configuration
- [ ] **Date/version** indicated
- [ ] **Critical cards** have explanatory comments
- [ ] **Units clearly stated** in comments

---

## POST-RUN VALIDATION CHECKLIST

**File:** `______________________________.f06`
**Analyst:** `______________________________`
**Date:** `______________________________`

### 1. Execution Status

```bash
grep "FATAL\|ERROR" your_file.f06
grep "WARNING" your_file.f06
grep "JOB COMPLETE" your_file.f06
```

- [ ] **No FATAL errors** present
- [ ] **No critical ERRORs** (review all errors)
- [ ] **Warnings reviewed** and acceptable
- [ ] **JOB COMPLETE** message present

### 2. Input Echo Verification

```bash
grep "TABDMP1" your_file.f06
grep "PARAM.*KDAMP" your_file.f06
```

- [ ] **TABDMP1** appears in input echo (card was read)
- [ ] **PARAM KDAMP** appears in input echo
- [ ] **FLUTTER** card echoed correctly
- [ ] **MKAERO1** reduced frequencies echoed correctly

### 3. Modal Analysis Results

```bash
grep -A 50 "REAL EIGENVALUES" your_file.f06
```

- [ ] **Mode frequencies** reported
- [ ] **First mode frequency** reasonable:
  - [ ] Compare to analytical: f₁ = (π²/a²)√(D/m) / (2π)
  - [ ] Error <5% acceptable, <10% marginal, >10% investigate
- [ ] **Mode shapes** physically reasonable (if plotted)
- [ ] **No negative eigenvalues** (indicates instability)

**First mode validation:**

| Source | Frequency (Hz) | Difference |
|--------|----------------|------------|
| Analytical | _______ | - |
| NASTRAN | _______ | _______% |

### 4. Flutter Summary - Critical Validation

```bash
grep -A 30 "FLUTTER  SUMMARY" your_file.f06
```

#### A. Damping Values

- [ ] **Damping column is NON-ZERO** ← **MOST CRITICAL CHECK**
  - [ ] If all zeros → **ANALYSIS INVALID** - check TABDMP1 formatting
- [ ] **Damping varies with velocity**
  - [ ] Typically decreases as velocity increases
  - [ ] Should cross zero at flutter point
- [ ] **Damping magnitude reasonable**:
  - [ ] Positive damping: 0.01 to 0.05 (1-5%)
  - [ ] Near flutter: -0.01 to +0.01
  - [ ] Far from flutter: may be larger

**Example of VALID output:**
```
VELOCITY       DAMPING        FREQUENCY
1.5600E+05     2.9800E-02     2.1856E+01  ← Positive (stable)
2.4678E+05     1.4500E-02     2.1920E+01  ← Decreasing
3.3756E+05    -2.3400E-03     2.2015E+01  ← FLUTTER! (≈0)
4.2833E+05    -9.8700E-03     2.2134E+01  ← Negative (unstable)
```

**Example of INVALID output:**
```
VELOCITY       DAMPING        FREQUENCY
1.5600E+05     0.0000000E+00  2.1856E+01  ← ❌ ZERO!
2.4678E+05     0.0000000E+00  2.1856E+01  ← ❌ ALL ZEROS - INVALID
3.3756E+05     0.0000000E+00  2.1856E+01  ← ❌ CHECK TABDMP1
```

#### B. Frequency Variation

- [ ] **Frequency changes with velocity**
  - [ ] Typically increases (aeroelastic stiffening)
  - [ ] If constant → no aeroelastic coupling (check SPLINE, CAERO)
- [ ] **Frequency at flutter** reasonable:
  - [ ] Within 20% of natural frequency
  - [ ] Coalescence with other mode (if applicable)

#### C. Complex Eigenvalues

- [ ] **Imaginary part NON-ZERO**
  - [ ] If all zeros → no aerodynamic effects
- [ ] **Real part sign** matches damping sign:
  - [ ] Positive damping → negative real part (stable)
  - [ ] Negative damping → positive real part (unstable)

### 5. Flutter Point Detection

```bash
grep -i "POINT OF FLUTTER\|CRITICAL" your_file.f06
```

- [ ] **Flutter point message** present
- [ ] **Critical velocity** reported
- [ ] **Flutter frequency** reported
- [ ] **Mode number** identified

**If NO flutter detected:**
- [ ] Velocity range sufficient? (extend FLFACT 3)
- [ ] Damping approaching zero at high velocities?
- [ ] Check for warnings about convergence

### 6. Flutter Speed Validation

**Extract critical velocity:** _______ mm/s = _______ m/s

**Compare to analytical predictions:**

| Method | Predicted V_flutter | Source |
|--------|---------------------|--------|
| Reduced Frequency (k=0.3) | _______ m/s | ω₁×a/k |
| Dynamic Pressure | _______ m/s | √(2q/ρ) |
| Historical Data | _______ m/s | Similar aircraft |
| **NASTRAN SOL145** | _______ m/s | **F06 output** |

**Assessment:**

- [ ] ✅ **Within ±20% of analytical** → Excellent agreement
- [ ] ⚠️ **Within ±30% of analytical** → Acceptable, document reasons
- [ ] ❌ **>30% difference** → Investigate discrepancy before accepting

**If outside expected range:**
- [ ] Check structural model (E, ρ, h, mesh)
- [ ] Check aerodynamic model (MKAERO1, CAERO panel count)
- [ ] Check boundary conditions (SSSS vs CCCC makes large difference)
- [ ] Verify units are consistent
- [ ] Compare to additional analytical methods
- [ ] Consider running alternative code (ZAERO, hand calculations)

### 7. Reduced Frequency Check

```
k_flutter = ω_flutter × a / V_flutter
```

**Calculate:**
- ω_flutter = 2π × f_flutter = _______ rad/s
- a (reference length) = _______ m
- V_flutter = _______ m/s
- **k_flutter = _______**

**Expected range:**
- [ ] **0.1 to 0.5** → Typical for subsonic panel flutter
- [ ] **<0.1** → Questionable (very low frequency or high speed)
- [ ] **>0.5** → Questionable (very high frequency or low speed)

### 8. Physical Consistency Checks

- [ ] **Flutter speed increases** with:
  - [ ] Increasing stiffness (E, h³)
  - [ ] Decreasing density (ρ_structure, ρ_air)
  - [ ] Increasing damping
- [ ] **Flutter mechanism** makes sense:
  - [ ] Panel flutter: single bending mode
  - [ ] Wing flutter: bending-torsion coupling
  - [ ] Control surface: hinge-mode coupling
- [ ] **Mode shape** at flutter is expected dominant mode

### 9. Sensitivity Assessment (If Performed)

```bash
# Run multiple cases with varied parameters
```

**Parameter variations:**

| Parameter | Baseline | -10% | +10% | V_flutter Change |
|-----------|----------|------|------|------------------|
| E (stiffness) | | | | ±____% |
| ρ (density) | | | | ±____% |
| h (thickness) | | | | ±____% |
| g (damping) | | | | ±____% |
| M (Mach) | | | | ±____% |

**Assessment:**
- [ ] **Most sensitive parameter** identified: _______
- [ ] **Sensitivity reasonable** (expected trends)
- [ ] **Uncertainty quantified** (if required)

### 10. Safety Margin Calculation

**Per MIL-A-8870C Section 3.3.1:**

```
Safety Factor = V_flutter / V_max_operational
```

**Calculate:**
- V_flutter (analysis) = _______ m/s
- V_max (operational) = _______ m/s
- **Safety Factor = _______**

**Requirement:**
- [ ] **SF ≥ 1.15** (15% margin minimum) per MIL-A-8870C
- [ ] **SF ≥ 1.20** (20% margin recommended for new designs)

**If margin insufficient:**
- [ ] Reduce operational speed envelope
- [ ] Increase structural stiffness (thickness, material)
- [ ] Add damping treatments
- [ ] Modify aerodynamic configuration
- [ ] Require flight test flutter clearance

---

## ACCEPTANCE CRITERIA

### Minimum Requirements for Valid Analysis

**MUST PASS ALL:**

1. ✅ **No fatal errors** in F06
2. ✅ **Damping is NON-ZERO** at all velocities
3. ✅ **Damping varies** with velocity (not constant)
4. ✅ **Frequency variation** observed (aeroelastic coupling present)
5. ✅ **Flutter point detected** and reported (if within velocity range)
6. ✅ **Flutter speed within ±30%** of analytical prediction

**IF ANY FAIL → ANALYSIS INVALID - DO NOT PROCEED**

### Additional Requirements for Certification

7. ⚠️ **Frequency error <5%** vs GVT or refined analytical
8. ⚠️ **Multi-method agreement** (<15% spread)
9. ⚠️ **Safety margin ≥15%** per MIL-A-8870C
10. ⚠️ **Sensitivity analysis** performed and documented
11. ⚠️ **Benchmark validation** against standard test cases

**IF ANY FAIL → Additional validation required before certification**

---

## RED FLAGS - STOP AND INVESTIGATE

**Immediate rejection criteria:**

🚩 **All damping values = 0** → Check TABDMP1 formatting
🚩 **Frequency constant across all velocities** → Check SPLINE, CAERO
🚩 **No flutter detected** with extended velocity range → Check model
🚩 **Flutter speed <50% of analytical** → Major model error
🚩 **Flutter speed >200% of analytical** → Major model error
🚩 **Negative frequencies** → Structural instability (divergence)
🚩 **Fatal errors** in F06 → Fix errors before proceeding
🚩 **Grid point singularities** → Check boundary conditions

---

## DOCUMENTATION REQUIREMENTS

### For Certification Package

Include in technical report:

- [ ] **Input file** (BDF) with comments
- [ ] **Output file** (F06) complete
- [ ] **V-g-f plot** (velocity-damping-frequency)
- [ ] **Mode shapes** at flutter point
- [ ] **Frequency comparison** table (analytical vs NASTRAN)
- [ ] **Flutter speed comparison** (multi-method)
- [ ] **Sensitivity analysis** results
- [ ] **Safety margin** calculation
- [ ] **Validation against benchmarks** (AGARD 445.6, etc.)
- [ ] **Compliance matrix** (MIL-A-8870C, FAA AC 25.629-1B)
- [ ] **Engineering judgment** statement and approval signatures

---

## EXAMPLE: COMPLETED CHECKLIST

### Panel Configuration
- **Geometry:** 500mm × 400mm × 3mm aluminum panel
- **Material:** Al 6061-T6 (E=71.7 GPa, ρ=2810 kg/m³)
- **Boundary:** SSSS (simply supported all edges)
- **Flight:** Mach 0.8, altitude 10,000m

### Pre-Run Validation (Example)
- [x] SOL 145 specified
- [x] PARAM KDAMP 1 present
- [x] TABDMP1 with g=0.03 (3% damping)
- [x] FLUTTER PK method, FLFACT 1=0.5, 2=0.8, 3=100-2500 m/s
- [x] MKAERO1 with k=0.001, 0.01, 0.1, 0.2, 0.4
- [x] CAERO1 8×8 panels for DLM
- [x] SPLINE1 to all 121 structural grids
- [x] Units: mm-kg-s-N (consistent)

### Post-Run Validation (Example)
- [x] No fatal errors
- [x] TABDMP1 in echo section
- [x] Damping NON-ZERO: ranges from +0.030 to -0.010
- [x] Frequency varies: 21.86 Hz to 22.46 Hz
- [x] Flutter detected at V=337 m/s
- [x] Analytical prediction: 250-450 m/s → ✅ Within range
- [x] Reduced frequency: k=0.28 → ✅ Typical for DLM
- [x] Safety margin: (337/280 - 1) = 20.4% → ✅ >15% required

**Status:** ✅ **ANALYSIS VALID - Acceptable for preliminary design**

**Further validation needed for certification:**
- GVT frequency correlation
- AGARD 445.6 benchmark
- Alternative flutter code comparison
- Sensitivity analysis

---

## REVISION HISTORY

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-11 | Initial checklist created | Senior Aeroelasticity Engineer |

---

## REFERENCES

1. **MIL-A-8870C** - Airplane Strength and Rigidity - Flutter, Divergence, and Other Aeroelastic Instabilities
2. **FAA AC 25.629-1B** - Means of Compliance with Title 14 CFR Part 25, Section 25.629
3. **EASA CS-25.629** - Aeroelastic Stability Requirements
4. **MSC Nastran Aeroelastic Analysis User's Guide**
5. **NASA TP-2000-209136** - Panel Flutter Prediction Methods
6. **Dowell, E.H. et al.** - A Modern Course in Aeroelasticity (5th ed.)

---

**END OF CHECKLIST**
