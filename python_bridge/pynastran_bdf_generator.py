"""
PyNastran-based BDF Generator for SOL145 Flutter Analysis
=========================================================

This module creates NASTRAN BDF files using pyNastran to ensure
proper formatting and eliminate fatal errors in NASTRAN execution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import datetime
import logging
import numpy as np

# Import pyNastran components
from pyNastran.bdf.bdf import BDF


def format_nastran_float(value: float) -> float:
    """
    CRITICAL FIX: Format float values to avoid scientific notation parsing issues
    NASTRAN expects proper float formatting without concatenation

    Args:
        value: Float value to format

    Returns:
        Properly formatted float for NASTRAN
    """
    # Ensure we don't get problematic formats like '7.17+10' or concatenated values
    if value is None or not isinstance(value, (int, float)):
        return 0.0

    # Convert to float to ensure proper type
    value = float(value)

    if abs(value) < 1e-10:
        return 0.0
    elif abs(value) > 1e15 or abs(value) < 1e-10:
        # For very large/small numbers, format properly
        formatted = f"{value:.3E}"
        return float(formatted.replace('+', '').replace('-', '-'))
    else:
        # For normal range numbers, use standard float
        return round(float(value), 6)

logger = logging.getLogger(__name__)


@dataclass
class PanelConfig:
    """Panel configuration for BDF generation"""
    length: float  # m
    width: float   # m
    thickness: float  # m
    nx: int  # elements in x direction
    ny: int  # elements in y direction
    material_id: int = 1
    property_id: int = 1


@dataclass
class MaterialConfig:
    """Material properties for BDF (SI units: m-kg-s-N)"""
    youngs_modulus: float  # Pa (N/m^2)
    poissons_ratio: float  # dimensionless
    density: float  # kg/m^3
    shear_modulus: Optional[float] = None  # Pa (N/m^2)
    material_id: int = 1


@dataclass
class AeroConfig:
    """Aerodynamic configuration for BDF (SI units: m-kg-s-N)"""
    mach_number: float
    reference_velocity: float  # m/s
    reference_chord: float  # m
    reference_density: float  # kg/m^3
    reduced_frequencies: List[float] = None
    velocities: List[float] = None  # m/s


class PyNastranBDFGenerator:
    """NASTRAN BDF file generator using pyNastran for SOL145 flutter analysis"""

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = None

    def generate_bdf(
        self,
        panel: PanelConfig,
        material: MaterialConfig,
        aero: AeroConfig,
        boundary_conditions: str = "SSSS",
        n_modes: int = 10,
        output_filename: str = "flutter_analysis.bdf"
    ) -> str:
        """Generate a NASTRAN BDF file for SOL145 flutter analysis using pyNastran"""

        # Initialize new BDF model
        self.model = BDF(debug=False)

        # Set units to SI (m-kg-s-N)
        self.model.units = ['m', 'kg', 's', 'N']

        filepath = self.output_dir / output_filename

        logger.info(f"Generating SOL145 BDF file using pyNastran: {filepath}")
        logger.info(f"Panel: {panel.length:.3f}m x {panel.width:.3f}m x {panel.thickness:.3f}m")
        logger.info(f"Mesh: {panel.nx}x{panel.ny} elements")

        # Add executive control
        self._add_executive_control()

        # Add case control
        self._add_case_control()

        # Add bulk data
        self._add_parameters()
        self._add_materials(material)
        self._add_properties(panel, material)
        self._add_grid_points(panel)
        self._add_elements(panel)
        self._add_boundary_conditions(panel, boundary_conditions)
        self._add_eigenvalue_extraction(n_modes)
        self._add_aerodynamic_cards(panel, aero)
        self._add_flutter_cards(aero, n_modes)

        # Write BDF file
        self.model.write_bdf(str(filepath), size=8, is_double=False, enddata=True)

        # DISABLED: Use CAERO1 (Doublet Lattice) for ALL Mach numbers
        # CAERO5 (Piston Theory) produces zero damping in MSC NASTRAN 2019.0
        # Post-process: For M>=0.7, replace CAERO1 with CAERO5 as raw text
        # This bypasses pyNastran API issues with PAERO5/AEFACT
        # Piston theory valid for M >= 0.7 (transonic/supersonic panel flutter)
        # if aero.mach_number >= 0.7:
        #     self._inject_caero5_raw(filepath, panel, aero)

        # Validate the BDF (temporarily disabled for debugging)
        # self._validate_bdf_file(filepath)

        logger.info(f"Successfully generated BDF file: {filepath}")
        return str(filepath)

    def _inject_caero5_raw(self, filepath: Path, panel: PanelConfig, aero: AeroConfig):
        """
        Inject CAERO5 cards as raw BDF text to bypass pyNastran API issues

        This replaces any CAERO1/PAERO1 cards with CAERO5/PAERO5 for M>=0.7
        (transonic/supersonic panel flutter requires piston theory)
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Remove pyNastran-generated aerodynamic cards
            lines_to_remove = [
                'CAERO1', 'PAERO1', 'MKAERO1', 'CAERO5', 'PAERO5', 'MKAERO2',
                'AEFACT', 'SPLINE'
            ]

            lines = content.split('\n')
            filtered_lines = []
            skip_continuation = False

            for line in lines:
                # Skip aerodynamic cards and their continuations
                if any(line.strip().startswith(card) for card in lines_to_remove):
                    skip_continuation = True
                    continue
                elif skip_continuation and line.startswith(' '):
                    continue
                else:
                    skip_continuation = False
                    filtered_lines.append(line)

            # Find insertion point (before ENDDATA)
            enddata_idx = None
            for i, line in enumerate(filtered_lines):
                if 'ENDDATA' in line:
                    enddata_idx = i
                    break

            if enddata_idx is None:
                enddata_idx = len(filtered_lines)

            # Build CAERO5 section as raw text
            caero5_section = self._build_caero5_raw_text(panel, aero)

            # Insert CAERO5 section
            filtered_lines.insert(enddata_idx, caero5_section)

            # Write back
            with open(filepath, 'w') as f:
                f.write('\n'.join(filtered_lines))

            logger.info(f"Injected CAERO5/Piston Theory cards for M={aero.mach_number:.2f}")

        except Exception as e:
            logger.error(f"Failed to inject CAERO5: {e}")
            raise

    def _build_caero5_raw_text(self, panel: PanelConfig, aero: AeroConfig) -> str:
        """Build CAERO5 section as properly formatted BDF text"""

        # Calculate dimensions (Z=0 for mid-plane aerodynamic reference)
        p1_x, p1_y, p1_z = 0.0, 0.0, 0.0
        p4_x, p4_y, p4_z = 0.0, panel.width, 0.0
        x12 = panel.length
        x43 = panel.length
        nspan = panel.ny

        # Build spanwise distribution AEFACT matching pyNastran format
        span_fractions = [f"{i/nspan:.4f}" for i in range(nspan + 1)]
        span_line1 = "AEFACT      3001" + "".join(f"{span_fractions[i]:>8}" for i in range(min(6, len(span_fractions))))
        span_continuation = ""
        if len(span_fractions) > 6:
            remaining = span_fractions[6:]
            for i in range(0, len(remaining), 8):
                chunk = remaining[i:i+8]
                # Continuation: blank field 1 (8 chars), data starts in field 2
                span_continuation += "\n" + " " * 8 + "".join(f"{v:>8}" for v in chunk)

        # Build raw BDF text matching working example format
        # NASTRAN uses fixed 8-character fields with compact notation
        def fmt_nastran(val):
            """Format float for NASTRAN fixed-field (8 chars)"""
            if abs(val) < 1e-10:
                return "      0."
            # Format to 4 decimal places, then strip trailing zeros
            s = f"{val:.4f}".rstrip('0').rstrip('.')
            # Add decimal point if integer
            if '.' not in s:
                s += '.'
            # For values < 1, use compact notation (.001 not 0.001)
            if abs(val) < 1.0 and s.startswith('0.'):
                s = s[1:]  # Remove leading 0
            return f"{s:>8}"

        p1_str = fmt_nastran(p1_x) + fmt_nastran(p1_y) + fmt_nastran(p1_z) + fmt_nastran(x12)
        p4_str = fmt_nastran(p4_x) + fmt_nastran(p4_y) + fmt_nastran(p4_z) + fmt_nastran(x43)

        # Build PAERO5 for piston theory (Table 9-32: thickness method, no control surfaces)
        # NALPHA=1, LALPHA=3002 (Mach-alpha), NXIS=1, LXIS=3003 (chord), NTAUS=1, LTAUS=3004 (thickness)
        caoci_entries = [0.0] * nspan
        paero5_text = "PAERO5      2001       1    3002       1    3003       1    3004\n"
        # Add CAOCI entries (all 0.0 for no control surfaces)
        # Continuation: blank field 1 (8 chars), data starts in field 2
        for i in range(0, len(caoci_entries), 8):
            chunk = caoci_entries[i:i+8]
            paero5_text += " " * 8 + "".join(f"{v:>8.1f}" for v in chunk) + "\n"

        # AEFACT entries per PAERO5 documentation
        # 3002: Mach-alpha pair (format: m1, α1 for NALPHA=1)
        # 3003: Chord coordinates ξm, ξh (midpoint=0.5, hinge=0.0 for no control surface)
        # 3004: Thickness ratios τm, τh, τt where τ = thickness/chord
        thickness_ratio = panel.thickness / panel.length
        aefact_alpha = f"AEFACT      3002{aero.mach_number:>8.2f}{0.0:>8.1f}\n"
        aefact_alpha += f"AEFACT      3003{0.5:>8.1f}{0.0:>8.1f}\n"
        aefact_alpha += f"AEFACT      3004{thickness_ratio:>8.4f}{thickness_ratio:>8.4f}{thickness_ratio:>8.4f}"

        # Calculate SPLINE1 BOX2: last aerodynamic box ID
        caero_id = 1001
        box2_id = caero_id + nspan - 1  # CAERO5 creates nspan boxes: 1001, 1002, ..., 1001+nspan-1

        # Build line by line to control exact spacing (avoid f-string indentation)
        # CRITICAL: Set NSPAN=0 to use LSPAN (AEFACT distribution)
        # If NSPAN>0, NASTRAN ignores LSPAN and uses equal strips!
        bdf_lines = [
            f"$AERO - Piston Theory for Supersonic Flutter (M={aero.mach_number:.2f})",
            f"CAERO5      1001    2001                   3001       0       0",
            " " * 8 + p1_str + p4_str,  # Child line: 8 spaces (field 1) + data fields
            paero5_text.rstrip('\n'),
            span_line1,
        ]
        if span_continuation:
            bdf_lines.append(span_continuation.lstrip('\n'))
        if aefact_alpha:
            bdf_lines.append(aefact_alpha)
        bdf_lines.extend([
            f"SPLINE1        1    1001    1001{box2_id:>8}       1",
            f"MKAERO2    {aero.mach_number:>5.2f}   .001",
            ""  # Empty line at end
        ])
        bdf_text = '\n'.join(bdf_lines)
        return bdf_text

    def _add_executive_control(self):
        """Add executive control section"""
        self.model.executive_control_lines = [
            'SOL 145',
            'CEND'
        ]

    def _add_case_control(self):
        """Add case control section using proper pyNastran case control deck"""
        from pyNastran.bdf.case_control_deck import CaseControlDeck

        # Create case control deck
        cc = CaseControlDeck([
            'TITLE = PyNastran Panel Flutter Analysis - SOL145',
            'ECHO = NONE',
            'SPC = 1',
            'METHOD = 1',
            'FMETHOD = 1',
            'DISPLACEMENT = ALL',
            'STRESS = ALL',
            'STRAIN = ALL',
            'FORCE = ALL',
            'BEGIN BULK'
        ])

        self.model.case_control_deck = cc

    def _add_parameters(self):
        """Add parameter cards"""
        # Essential parameters for flutter analysis
        self.model.add_param('COUPMASS', 1)
        self.model.add_param('GRDPNT', 0)
        # CRITICAL FIX: WTMASS must be 1.0 for SI units (m-kg-s-N)
        # 0.00259 is for English units (in-lbf-s) and causes 19.65x frequency error
        self.model.add_param('WTMASS', 1.0)  # SI units: mass density is used directly
        self.model.add_param('POST', -1)
        self.model.add_param('AUTOSPC', 'YES')

    def _add_materials(self, material: MaterialConfig):
        """Add material cards using pyNastran"""
        # Calculate shear modulus if not provided
        if material.shear_modulus is None:
            G = material.youngs_modulus / (2 * (1 + material.poissons_ratio))
        else:
            G = material.shear_modulus

        # CRITICAL FIX: Add MAT1 card with proper scientific notation formatting
        self.model.add_mat1(
            mid=material.material_id,
            E=format_nastran_float(material.youngs_modulus),  # FIXED: Proper E notation
            G=format_nastran_float(G),                        # FIXED: Proper E notation
            nu=format_nastran_float(material.poissons_ratio),
            rho=format_nastran_float(material.density),       # FIXED: Proper E notation
            a=0.0,      # Thermal expansion coefficient
            tref=0.0,   # Reference temperature
            ge=0.0,     # Structural damping
            St=0.0,     # Stress limit in tension
            Sc=0.0,     # Stress limit in compression
            Ss=0.0,     # Stress limit in shear
            mcsid=0     # Material coordinate system
        )

    def _add_properties(self, panel: PanelConfig, material: MaterialConfig):
        """Add property cards using pyNastran"""
        self.model.add_pshell(
            pid=panel.property_id,
            mid1=material.material_id,
            t=panel.thickness,
            mid2=None,  # Bending material
            twelveIt3=1.0,  # Bending moment of inertia ratio
            mid3=None,  # Transverse shear material
            tst=0.833333,  # Transverse shear thickness ratio
            nsm=0.0,  # Non-structural mass
            z1=None,  # Fiber distance for stress calculation
            z2=None,  # Fiber distance for stress calculation
            mid4=None  # Membrane-bending coupling material
        )

    def _add_grid_points(self, panel: PanelConfig):
        """Add grid points using pyNastran"""
        grid_id = 1
        dx = panel.length / panel.nx
        dy = panel.width / panel.ny

        for j in range(panel.ny + 1):
            for i in range(panel.nx + 1):
                x = i * dx
                y = j * dy
                z = 0.0

                self.model.add_grid(
                    nid=grid_id,
                    xyz=[x, y, z],
                    cp=0,  # Coordinate system
                    cd=0,  # Analysis coordinate system
                    ps='',  # Permanent single-point constraints
                    seid=0  # Superelement ID
                )
                grid_id += 1

    def _add_elements(self, panel: PanelConfig):
        """Add CQUAD4 elements using pyNastran"""
        elem_id = 1

        for j in range(panel.ny):
            for i in range(panel.nx):
                # Calculate node IDs for this element
                n1 = j * (panel.nx + 1) + i + 1
                n2 = n1 + 1
                n3 = n1 + panel.nx + 2
                n4 = n1 + panel.nx + 1

                self.model.add_cquad4(
                    eid=elem_id,
                    pid=panel.property_id,
                    nids=[n1, n2, n3, n4],
                    theta_mcid=0.0,  # Material angle
                    zoffset=0.0,  # Offset
                    tflag=0,  # Membrane thickness flag
                    T1=None, T2=None, T3=None, T4=None  # Thicknesses at nodes
                )
                elem_id += 1

    def _add_boundary_conditions(self, panel: PanelConfig, boundary_conditions: str):
        """Add boundary condition cards using pyNastran"""
        # Handle boundary condition string (e.g., 'SSSS', 'CCCC', 'CFFF')
        if hasattr(boundary_conditions, 'value'):
            bc_str = boundary_conditions.value
        else:
            bc_str = str(boundary_conditions)

        if bc_str.upper() == "SSSS":  # Simply supported on all edges
            # For SSSS boundary conditions on a plate:
            # - All edge nodes: W = 0 (out-of-plane deflection)
            # - Corner nodes: Additional in-plane constraints for stability

            # Collect edge nodes
            edge_nodes = []

            # Bottom edge (j=0)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Top edge (j=ny)
            for i in range(panel.nx + 1):
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            # Left edge (i=0) - skip corners to avoid duplicates
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx) - skip corners to avoid duplicates
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            # Remove duplicates and sort
            edge_nodes = sorted(set(edge_nodes))

            # SSSS: Simply supported - W = 0 on all edges
            self.model.add_spc1(
                conid=1,
                components='3',  # W (out-of-plane deflection)
                nodes=edge_nodes
            )

            # Corner constraints for rigid body mode prevention
            # Bottom-left corner: fix U, V (in-plane motion)
            corner_bl = 1
            self.model.add_spc1(
                conid=1,
                components='12',  # U, V (in-plane)
                nodes=[corner_bl]
            )

            # Bottom-right corner: fix V only (prevent Y-direction rigid body)
            corner_br = panel.nx + 1
            self.model.add_spc1(
                conid=1,
                components='2',  # V (Y-direction)
                nodes=[corner_br]
            )

        elif bc_str.upper() == "CCCC":  # Clamped on all edges
            # Clamped: constrain all translations and rotations on all edges
            edge_nodes = []

            # Bottom edge (j=0)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Top edge (j=ny)
            for i in range(panel.nx + 1):
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            # Left edge (i=0) - skip corners to avoid duplicates
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx) - skip corners to avoid duplicates
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            # Remove duplicates and sort
            edge_nodes = sorted(set(edge_nodes))

            # CCCC: Clamped - all DOFs constrained on all edges
            self.model.add_spc1(
                conid=1,
                components='123456',  # All DOFs
                nodes=edge_nodes
            )

        elif bc_str.upper() == "CFFF":  # Cantilever
            # Cantilever: clamped at x=0, free elsewhere
            left_edge_nodes = []

            # Left edge only (i=0, all j)
            for j in range(panel.ny + 1):
                left_edge_nodes.append(j * (panel.nx + 1) + 1)

            # CFFF: Clamped at left edge
            self.model.add_spc1(
                conid=1,
                components='123456',  # All DOFs
                nodes=left_edge_nodes
            )

        elif bc_str.upper() == "CFCF":  # Clamped-Free-Clamped-Free
            # Clamped at x=0 and x=length, free at y=0 and y=width
            edge_nodes = []

            # Left edge (i=0, all j)
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx, all j)
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            # Remove duplicates and sort
            edge_nodes = sorted(set(edge_nodes))

            # CFCF: Clamped at left and right edges
            self.model.add_spc1(
                conid=1,
                components='123456',  # All DOFs
                nodes=edge_nodes
            )

        elif bc_str.upper() == "SCSC":  # Simply supported-Clamped-Simply supported-Clamped
            # Left and right edges: Simply supported (DOF 3 only)
            ss_edge_nodes = []
            for j in range(panel.ny + 1):
                ss_edge_nodes.append(j * (panel.nx + 1) + 1)  # Left edge
                ss_edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)  # Right edge
            ss_edge_nodes = sorted(set(ss_edge_nodes))

            self.model.add_spc1(
                conid=1,
                components='3',  # W only
                nodes=ss_edge_nodes
            )

            # Bottom and top edges: Clamped (DOF 123456) - excluding corners
            c_edge_nodes = []
            for i in range(1, panel.nx):  # Skip corners
                c_edge_nodes.append(i + 1)  # Bottom edge
                c_edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)  # Top edge

            if c_edge_nodes:
                self.model.add_spc1(
                    conid=1,
                    components='123456',  # All DOFs
                    nodes=c_edge_nodes
                )

            # Corner constraints for rigid body modes
            corner_bl = 1
            self.model.add_spc1(
                conid=1,
                components='12',  # U, V
                nodes=[corner_bl]
            )

        else:
            # Unknown boundary condition - default to SSSS with warning
            logger.warning(f"Unknown boundary condition '{bc_str}' - defaulting to SSSS")

            # Default to SSSS implementation
            edge_nodes = []
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)
            edge_nodes = sorted(set(edge_nodes))

            self.model.add_spc1(
                conid=1,
                components='3',
                nodes=edge_nodes
            )

            corner_bl = 1
            corner_br = panel.nx + 1
            self.model.add_spc1(conid=1, components='12', nodes=[corner_bl])
            self.model.add_spc1(conid=1, components='2', nodes=[corner_br])

    def _add_eigenvalue_extraction(self, n_modes: int):
        """Add eigenvalue extraction cards using pyNastran"""
        self.model.add_eigrl(
            sid=1,
            v1=None,  # Lower eigenvalue bound
            v2=None,  # Upper eigenvalue bound
            nd=n_modes,  # Number of desired eigenvalues
            msglvl=0,  # Message level
            maxset=None,  # Maximum number of vectors in block
            shfscl=None,  # Shift point
            norm=None,  # Normalization method
            options=None,  # Solution options
            values=None  # Specific eigenvalue bounds
        )

    def _add_aerodynamic_cards(self, panel: PanelConfig, aero: AeroConfig):
        """
        Add aerodynamic reference cards using pyNastran

        CRITICAL FIX (Oct 2025): Root cause of zero damping identified:
        - PyNastran CAERO5 API generates malformed BDF cards
        - This forced fallback to CAERO1 (Doublet Lattice)
        - CAERO1 CANNOT model panel flutter (only lifting surfaces)
        - Result: Zero damping

        Solution: Use template-based generation for CAERO5 (M >= 0.7)
        - Bypasses pyNastran formatting bugs
        - Enables piston theory for panel flutter
        - Reference: flutter_example.pdf shows CAERO5 produces non-zero damping
        """
        # Add AERO card for flutter analysis (required for SOL145)
        # CRITICAL: AERO (not AEROS) is required for SOL145 flutter analysis
        # AEROS is for static aeroelasticity (SOL144)
        # AERO is for dynamic aeroelasticity (SOL145/146)
        self.model.add_aero(
            acsid=0,  # Aerodynamic coordinate system
            velocity=None,  # Must be blank for SOL145 flutter - velocities from FLUTTER/FLFACT
            cref=aero.reference_chord,  # Reference chord
            rho_ref=1.225,  # Reference air density (kg/m³ at sea level)
            sym_xz=0,  # No symmetry about XZ plane
            sym_xy=0   # No symmetry about XY plane
        )

        # For M >= 0.7: Use template-based CAERO5 generation (REQUIRED for panel flutter)
        # For M < 0.7: Use CAERO1 (Doublet Lattice - acceptable for subsonic)
        if aero.mach_number >= 0.7:
            logger.warning(f"Template-based CAERO5 required for M={aero.mach_number:.2f}")
            logger.warning("Falling back to CAERO1 - will produce zero/minimal damping")
            logger.warning("Use create_pynastran_flutter_bdf() with use_template=True")
            self._add_caero1_mesh(panel, aero)
        else:
            logger.info(f"Using CAERO1 (Doublet Lattice Method) for subsonic M={aero.mach_number:.2f}")
            self._add_caero1_mesh(panel, aero)

    def _add_caero1_mesh(self, panel: PanelConfig, aero: AeroConfig):
        """Add CAERO1 mesh for doublet lattice method (subsonic)"""
        caero_id = 1001
        pid = 3001

        # PAERO1 property
        self.model.add_paero1(pid=pid, caero_body_ids=None)

        # CAERO1 panel (Z=0 for mid-plane aerodynamic reference)
        p1 = [0.0, 0.0, 0.0]
        p4 = [0.0, panel.width, 0.0]
        x12 = panel.length
        x43 = panel.length

        self.model.add_caero1(
            eid=caero_id,
            pid=pid,
            igroup=1,
            p1=p1,
            x12=x12,
            p4=p4,
            x43=x43,
            cp=0,
            nspan=panel.ny,
            nchord=panel.nx,
            lspan=0,
            lchord=0,
            comment='Doublet Lattice Panel'
        )

        # Add spline to connect structure to aerodynamics
        self._add_splines(panel, caero_id)

        # Add MKAERO1 for aerodynamic matrix generation
        self._add_mkaero1(aero)

    def _add_caero5_mesh(self, panel: PanelConfig, aero: AeroConfig):
        """
        Add CAERO5 mesh for piston theory (M ≥ 0.7)

        Per MSC Nastran Aeroelastic Analysis User's Guide:
        - CAERO5 defines strip elements for piston theory aerodynamics
        - Valid for M >= 0.7 (transonic/supersonic/hypersonic flow)
        - REQUIRED for panel flutter analysis (CAERO1 cannot model panel flutter)
        - Provides direct aerodynamic loading without matrix interpolation
        - More efficient than ZONA51 for panel flutter

        Reference: flutter_example.pdf HA145HA (M=2.0, M=3.0)
        """
        caero_id = 1001
        paero_id = 2001
        aefact_span_id = 3001  # Spanwise strip distribution (for LSPAN)
        aefact_alpha_id = 3002  # Integration points for PAERO5 LALPHA

        # Add PAERO5 property card
        # PAERO5: Property card for CAERO5 piston theory elements
        # Format: PAERO5, PID, NALPHA, LALPHA, NXIS, LXIS, NTAUS, LTAUS
        # Per MSC Nastran: NALPHA must be > 0 (typically 1 for linear piston theory)
        # CRITICAL: caoci must have panel.ny entries (number of spanwise strips)
        # Each entry is the control surface influence coefficient for that strip
        caoci_entries = [0.0] * panel.ny  # No control surfaces, all zeros

        # Match working example exactly: NALPHA=1, LALPHA=3002
        self.model.add_paero5(
            pid=paero_id,
            caoci=caoci_entries,  # Control surface coeffs (must match NSPAN)
            nalpha=1,  # Exactly as in working example
            lalpha=aefact_alpha_id,  # Points to AEFACT 3002
            nxis=0,
            lxis=0,
            ntaus=0,
            ltaus=0
        )

        # Create AEFACT for spanwise strip distribution
        # For NSPAN strips, we need NSPAN+1 boundary positions
        span_positions = [i / panel.ny for i in range(panel.ny + 1)]
        self.model.add_aefact(sid=aefact_span_id, fractions=span_positions)

        # Create single-value AEFACT for alpha integration (exactly as in working example)
        self.model.add_aefact(sid=aefact_alpha_id, fractions=[0.0])

        # Add CAERO5 card
        # CAERO5: Aerodynamic panel for piston theory
        # Format: CAERO5, EID, PID, CP, NSPAN, LSPAN, NTHRY, NTHICK
        #         X1, Y1, Z1, X12, X4, Y4, Z4, X43
        p1 = [0.0, 0.0, 0.0]  # Leading edge left point (at mid-plane Z=0)
        p4 = [0.0, panel.width, 0.0]  # Leading edge right point (at mid-plane Z=0)
        x12 = panel.length  # Chord length
        x43 = panel.length  # Chord length (same for rectangular panel)

        # PyNastran add_caero5 has limited parameter support
        # Use basic parameters only
        # LSPAN references AEFACT for spanwise strip distribution
        self.model.add_caero5(
            eid=caero_id,
            pid=paero_id,
            nspan=panel.ny,  # Number of spanwise strips
            lspan=aefact_span_id,  # AEFACT ID for spanwise distribution (must be > 0)
            p1=p1,
            x12=x12,
            p4=p4,
            x43=x43,
            cp=0,  # Coordinate system
            comment='Piston Theory Panel for Supersonic Flutter'
        )

        # Add spline to connect structure to aerodynamics
        self._add_splines(panel, caero_id)

        # Add MKAERO2 for supersonic aerodynamic matrix generation
        self._add_mkaero2(aero)

    def _add_splines(self, panel: PanelConfig, caero_id: int):
        """Add spline cards for structure-aero coupling"""
        # Create SET1 for all structural nodes
        total_nodes = (panel.nx + 1) * (panel.ny + 1)
        node_list = list(range(1, total_nodes + 1))

        self.model.add_set1(sid=1, ids=node_list)

        # Add SPLINE1 for surface interpolation
        # Aerodynamic box IDs start from caero_id
        self.model.add_spline1(
            eid=1,
            caero=caero_id,
            box1=caero_id,  # First aerodynamic box
            box2=caero_id + panel.nx * panel.ny - 1,  # Last aerodynamic box
            setg=1,
            dz=0.0,
            method='IPS',
            usage='BOTH',
            nelements=10,
            melements=10
        )

    def _add_flutter_cards(self, aero: AeroConfig, n_modes: int):
        """
        Add flutter analysis cards using pyNastran

        Per NASTRAN manual pages 117-120:
        - PK method: British flutter method, treats aerodynamics as real frequency-dependent springs/dampers
        - Provides physical damping values (unlike K-method artificial damping)
        - Best for determining stability at specific velocities
        - IMETHOD='L': Linear interpolation for aerodynamic matrices

        Flutter card configuration:
        - DENSITY: FLFACT ID for density ratios (ρ/ρ_ref)
        - MACH: FLFACT ID for Mach numbers
        - REDUCED_FREQ_VELOCITY: FLFACT ID for velocities (PK method uses velocities, not k)
        """
        # Add FLUTTER card for PK method flutter analysis
        self.model.add_flutter(
            sid=1,
            method='PK',  # PK method: most robust for panel flutter
            density=11,   # FLFACT ID for density ratios
            mach=12,      # FLFACT ID for Mach numbers
            reduced_freq_velocity=13,  # FLFACT ID for velocities (m/s)
            imethod='L',  # Linear interpolation for aero matrices
            nvalue=n_modes,  # Number of modes to track
            omax=None,       # No limit on frequency (None = track all)
            epsilon=0.001,   # Convergence tolerance for PK iterations
            comment='PK Flutter Analysis for Panel'
        )

        # FLFACT 11: Density ratios
        # CRITICAL FIX: ρ/ρ_ref = 0.5 for ONE-SIDED FLOW (panel flutter)
        # Per MSC Nastran flutter_example.pdf HA145HA/HB:
        # "Uses 0.5 density factor for one-sided flow"
        # Aerodynamic pressure acts only on air side, not both sides of panel
        self.model.add_flfact(sid=11, factors=[0.5])

        # FLFACT 12: Mach numbers
        # Single Mach number per analysis (could extend for Mach sweep)
        self.model.add_flfact(sid=12, factors=[aero.mach_number])

        # FLFACT 13: Velocities for PK method flutter sweep
        # CRITICAL: PK method requires VELOCITIES (m/s), not reduced frequencies!
        # Per manual page 118: "velocities (PK-method)" in FLUTTER card description
        if aero.velocities and len(aero.velocities) > 0:
            # Use provided velocities (m/s)
            velocity_floats = [float(v) for v in aero.velocities]
            logger.info(f"Using {len(velocity_floats)} user-specified velocities for flutter sweep")
        else:
            # Calculate physics-based velocity range for panel flutter
            # Estimate flutter velocity range based on panel properties and Mach number
            #
            # Typical panel flutter occurs when dynamic pressure approaches:
            # q_flutter ≈ k * (E*t^3) / (L^2)  where k is a factor depending on boundary conditions
            #
            # For conservative coverage, sweep from low subsonic to hypersonic range
            # Adjust based on expected flutter speed if known

            # Default comprehensive velocity sweep (m/s)
            # Covers typical panel flutter range: 200-1000 m/s
            # Extended range ensures detection even for unusual configurations
            default_velocities = [
                50.0, 100.0, 150.0,        # Low velocity: structural modes dominant
                200.0, 250.0, 300.0,       # Transition: aeroelastic coupling begins
                350.0, 400.0, 450.0,       # Primary flutter range for many panels
                500.0, 550.0, 600.0,       # Extended flutter range
                650.0, 700.0, 800.0,       # High velocity: potential second flutter
                900.0, 1000.0, 1200.0      # Very high velocity: ensure stability check
            ]
            velocity_floats = default_velocities
            logger.info(f"Using default {len(velocity_floats)} velocities for comprehensive flutter sweep")

        # Add velocity FLFACT with validation
        # Ensure velocities are positive and sorted
        velocity_floats = sorted([v for v in velocity_floats if v > 0])

        if not velocity_floats:
            # Fallback if somehow all velocities were invalid
            velocity_floats = [100.0, 300.0, 500.0, 700.0, 1000.0]
            logger.warning("Invalid velocity list, using minimal fallback values")

        logger.info(f"Flutter velocity range: {velocity_floats[0]:.1f} to {velocity_floats[-1]:.1f} m/s ({len(velocity_floats)} points)")

        self.model.add_flfact(sid=13, factors=velocity_floats)

    def _add_mkaero1(self, aero: AeroConfig):
        """Add MKAERO1 cards for aerodynamic matrix generation (subsonic/transonic)"""
        # MKAERO1 defines Mach numbers and reduced frequencies for aerodynamic matrix calculations
        # Used with CAERO1 (Doublet Lattice Method)
        mach_numbers = [aero.mach_number]
        reduced_frequencies = [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]  # Standard range (must be > 0.0)

        self.model.add_mkaero1(
            machs=mach_numbers,
            reduced_freqs=reduced_frequencies
        )

    def _add_mkaero2(self, aero: AeroConfig):
        """
        Add MKAERO2 cards for supersonic aerodynamic matrix generation

        Per MSC Nastran Aeroelastic Analysis User's Guide:
        - MKAERO2 is used for supersonic flow with piston theory (CAERO5)
        - Defines Mach number and reduced frequency pairs
        - Only one reduced frequency needed for piston theory (typically k=0.001)
        - Reference: flutter_example.pdf HA145HA uses MKAERO2 for M=2.0, M=3.0
        """
        # For piston theory, we only need one reduced frequency point
        # Piston theory is direct time-domain, not frequency-domain like DLM
        # k=0.001 is standard for quasi-steady approximation
        mach = aero.mach_number
        k_reduced = 0.001  # Quasi-steady reduced frequency

        # MKAERO2 format: pairs of (Mach, k)
        self.model.add_mkaero2(
            machs=[mach],
            reduced_freqs=[k_reduced]
        )

        logger.info(f"Added MKAERO2: M={mach:.2f}, k={k_reduced:.3f} (piston theory)")

    def _validate_bdf_file(self, filepath: Path):
        """Validate the generated BDF file"""
        try:
            # Try to read the BDF file back
            test_model = BDF(debug=False)
            test_model.read_bdf(str(filepath), validate=True, xref=False)

            # Check for essential cards
            checks = {
                'Materials': len(test_model.materials) > 0,
                'Properties': len(test_model.properties) > 0,
                'Nodes': len(test_model.nodes) > 0,
                'Elements': len(test_model.elements) > 0,
                'SPCs': len(test_model.spcs) > 0,
                'Eigenvalue methods': len(test_model.methods) > 0
            }

            for check_name, passed in checks.items():
                if passed:
                    logger.info(f"✓ {check_name}: OK")
                else:
                    logger.warning(f"✗ {check_name}: Missing")

            logger.info("BDF validation completed successfully")

        except Exception as e:
            logger.error(f"BDF validation failed: {e}")
            raise


def create_pynastran_flutter_bdf(config: Dict[str, Any], output_dir: str = ".", use_template: bool = None) -> str:
    """
    Create a SOL145 flutter analysis BDF file

    Args:
        config: Configuration dictionary
        output_dir: Output directory
        use_template: Force template-based generation (auto-detects for M>=0.7 if None)

    Returns:
        Path to generated BDF file
    """

    mach = config.get('mach_number', 2.0)

    # Auto-detect: use template for M >= 0.7 (piston theory required)
    if use_template is None:
        use_template = (mach >= 0.7)

    if use_template:
        logger.info(f"Using template-based CAERO5 generation for M={mach:.2f}")
        from template_bdf_generator import TemplateBDFGenerator

        generator = TemplateBDFGenerator()
        return generator.generate_caero5_flutter_bdf(
            length=config.get('panel_length', 1.0),
            width=config.get('panel_width', 0.5),
            thickness=config.get('thickness', 0.0015),
            nx=config.get('nx', 20),
            ny=config.get('ny', 20),
            youngs_modulus=config.get('youngs_modulus', 71.7e9),
            poissons_ratio=config.get('poissons_ratio', 0.33),
            density=config.get('density', 2810.0),
            mach_number=mach,
            velocities=config.get('velocities', [550, 600, 650, 700, 750, 800]),
            output_file=str(Path(output_dir) / config.get('output_filename', 'flutter_analysis.bdf'))
        )
    else:
        logger.info(f"Using pyNastran CAERO1 generation for M={mach:.2f}")
        generator = PyNastranBDFGenerator(output_dir)

        # Extract panel config
        panel = PanelConfig(
            length=config.get('panel_length', 1.0),  # m
            width=config.get('panel_width', 0.5),    # m
            thickness=config.get('thickness', 0.0015),  # m
            nx=config.get('nx', 20),
            ny=config.get('ny', 20)
        )

        # Extract material config (SI units: m-kg-s-N)
        material = MaterialConfig(
            youngs_modulus=config.get('youngs_modulus', 71.7e9),  # Pa
            poissons_ratio=config.get('poissons_ratio', 0.33),
            density=config.get('density', 2810.0)  # kg/m^3
        )

        # Extract aero config
        aero = AeroConfig(
            mach_number=mach,
            reference_velocity=config.get('velocity', 600.0),  # m/s
            reference_chord=config.get('panel_length', 1.0),  # m
            reference_density=1.225,  # kg/m^3 (air at sea level)
            reduced_frequencies=config.get('reduced_frequencies', [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]),
            velocities=config.get('velocities')  # m/s
        )

        # Generate BDF
        return generator.generate_bdf(
            panel=panel,
            material=material,
            aero=aero,
            boundary_conditions=config.get('boundary_conditions', 'SSSS'),
            n_modes=config.get('n_modes', 20),
            output_filename=config.get('output_filename', 'pynastran_flutter.bdf')
        )


if __name__ == "__main__":
    # Test the generator
    test_config = {
        'panel_length': 1.0,    # 1.0 m
        'panel_width': 0.5,     # 0.5 m
        'thickness': 0.002,     # 2 mm
        'nx': 10,
        'ny': 10,
        'youngs_modulus': 71.7e9,  # Aluminum
        'poissons_ratio': 0.33,
        'density': 2810,
        'mach_number': 0.8,  # Subsonic to use CAERO1 instead of CAERO5
        'velocity': 300.0,
        'n_modes': 15,
        'boundary_conditions': 'SSSS',
        'output_filename': 'test_pynastran_flutter.bdf'
    }

    bdf_file = create_pynastran_flutter_bdf(test_config, ".")
    print(f"Generated BDF file: {bdf_file}")