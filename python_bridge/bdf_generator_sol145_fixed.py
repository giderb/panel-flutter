"""
NASTRAN BDF File Generator for SOL145 Flutter Analysis
=====================================================

Generates validated NASTRAN Bulk Data Files for panel flutter analysis using
doublet lattice method (CAERO1) for reliable aerodynamic modeling.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PanelConfig:
    """Panel configuration for BDF generation"""
    length: float  # mm
    width: float   # mm
    thickness: float  # mm
    nx: int  # elements in x direction
    ny: int  # elements in y direction
    material_id: int = 1
    property_id: int = 1
    structural_damping: float = 0.005  # CRITICAL FIX v2.14.0: Realistic Al damping (0.5% not 3%)


@dataclass
class MaterialConfig:
    """Material properties for BDF (NASTRAN mm-tonne-s-N system)"""
    youngs_modulus: float  # MPa (N/mm^2)
    poissons_ratio: float  # dimensionless
    density: float  # tonne/mm^3 (Mg/mm^3) = original_kg_per_m3 * 1e-12
    shear_modulus: Optional[float] = None  # MPa (N/mm^2)
    material_id: int = 1


@dataclass
class AeroConfig:
    """Aerodynamic configuration for BDF (NASTRAN mm-tonne-s-N system)"""
    mach_number: float
    reference_velocity: float  # mm/s
    reference_chord: float  # mm
    reference_density: float  # tonne/mm^3 (Mg/mm^3) = kg/m^3 * 1e-12
    altitude: float = 10000  # meters (for proper density calculation)
    reduced_frequencies: List[float] = None
    velocities: List[float] = None  # mm/s
    piston_theory_order: int = 1  # CRITICAL: Piston theory order (1, 2, or 3) for CAERO5 NTHRY field


class Sol145BDFGenerator:
    """NASTRAN BDF file generator for SOL145 flutter analysis with correct piston theory"""

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_bdf(
        self,
        panel: PanelConfig,
        material: MaterialConfig,
        aero: AeroConfig,
        boundary_conditions: str = "SSSS",
        n_modes: int = 10,
        output_filename: str = "flutter_analysis.bdf",
        aerodynamic_theory: Optional[str] = None,
        material_object: Optional[Any] = None,
        piston_theory_order: int = 1  # CRITICAL: Piston theory order for CAERO5 NTHRY field
    ) -> str:
        """Generate a NASTRAN BDF file for SOL145 flutter analysis with correct cards

        Args:
            piston_theory_order: Piston theory order (1, 2, or 3) for CAERO5 NTHRY field.
                                 Only used when aerodynamic_theory='PISTON_THEORY'.
                                 Default: 1 (linear piston theory)
        """

        filepath = self.output_dir / output_filename
        lines = []

        # CRITICAL: Store piston theory order in aero config for CAERO5 generation
        aero.piston_theory_order = piston_theory_order
        logger.info(f"Piston Theory Order: {piston_theory_order}")

        # Check if we have a composite laminate
        is_composite = (material_object is not None and
                       type(material_object).__name__ == 'CompositeLaminate')

        # Header comments
        lines.append("$ NASTRAN SOL145 FLUTTER ANALYSIS - CORRECTED PISTON THEORY")
        lines.append(f"$ Generated: {datetime.datetime.now()}")
        lines.append(f"$ Panel: {panel.length}mm x {panel.width}mm")
        lines.append(f"$ Mach number: {aero.mach_number}")
        lines.append("$")

        # Executive control
        lines.append("SOL 145")
        lines.append("CEND")

        # Case control
        lines.append("TITLE = Panel Flutter Analysis - Piston Theory")
        lines.append("ECHO = NONE")
        lines.append("SPC = 1")
        lines.append("METHOD = 1")
        lines.append("FMETHOD = 1")
        lines.append("BEGIN BULK")
        lines.append("$")

        # Parameters
        lines.append("PARAM   COUPMASS1")
        lines.append("PARAM   GRDPNT  0")
        lines.append("PARAM   AUTOSPC YES")
        lines.append("$ AUTOSPC: Automatically constrain singular DOFs (e.g., drilling rotation)")
        # PARAM VREF for velocity conversion (if velocities in in/s, converts to ft/s for output)
        lines.append("PARAM   VREF    1.0")  # Will be adjusted based on unit system

        # Structural Damping - CRITICAL FIX for NASTRAN 2019 bug
        # TABDMP1 is not applied correctly in SOL 145 PK method in some NASTRAN versions
        # CRITICAL FIX v2.1.9: Use configurable damping from panel config
        damping_ratio = panel.structural_damping  # Default 0.03 (3% critical damping)
        lines.append(f"PARAM   W3      {damping_ratio:.4f}")
        lines.append(f"$ W3={damping_ratio:.4f}: Uniform critical damping ratio on all modes")
        # Keep TABDMP1 for compatibility with newer NASTRAN versions
        lines.append("PARAM   KDAMP   1")
        lines.append("$ KDAMP=1: Use TABDMP1 with ID=1 (backup for NASTRAN versions that support it)")

        # PARAM OPPHIPA for higher-order piston theory (includes angle-of-attack effects)
        # Only add if using piston theory (checked later in code)
        if aerodynamic_theory == "PISTON_THEORY" or (aerodynamic_theory is None and aero.mach_number >= 1.5):
            lines.append("PARAM   OPPHIPA 1")
            lines.append("$ OPPHIPA=1: Use higher-order piston theory for better accuracy at M<3")
        lines.append("$")

        # Material and Property Cards - Handle isotropic vs composite
        if is_composite:
            lines.append("$ Composite Laminate Material Properties")
            lines.append(f"$ Laminate: {material_object.name}")
            lines.append(f"$ Total thickness: {material_object.total_thickness} mm")
            lines.append(f"$ Number of plies: {len(material_object.laminas)}")
            lines.append("$")

            # Write MAT8 cards for each unique material
            # Track unique materials to avoid duplicates
            unique_materials = {}
            mat_id = 1

            for lamina in material_object.laminas:
                mat_name = lamina.material.name
                if mat_name not in unique_materials:
                    unique_materials[mat_name] = (mat_id, lamina.material)
                    mat_id += 1

            # Write MAT8 cards
            lines.append("$ Orthotropic Material Cards (MAT8)")
            for mat_name, (mid, mat) in unique_materials.items():
                lines.append(f"$ Material: {mat_name}")
                # MAT8 format: MID E1 E2 NU12 G12 G1Z G2Z RHO
                # Convert from Pa to MPa (N/mm²)
                e1_mpa = mat.e1 / 1e6
                e2_mpa = mat.e2 / 1e6
                g12_mpa = mat.g12 / 1e6
                g1z_mpa = (mat.g1z / 1e6) if mat.g1z else g12_mpa
                g2z_mpa = (mat.g2z / 1e6) if mat.g2z else (g12_mpa * 0.5)
                # CRITICAL FIX: Use 1e-12 for tonne/mm³ (consistent with MAT1)
                # Previous bug used 1e-9 (kg/mm³) which was inconsistent with isotropic materials
                rho_tonne_mm3 = mat.density * 1e-12  # kg/m³ to tonne/mm³

                lines.append(f"MAT8    {mid:<8}{e1_mpa:<8.1f}{e2_mpa:<8.1f}{mat.nu12:<8.3f}{g12_mpa:<8.1f}{g1z_mpa:<8.1f}{g2z_mpa:<8.1f}{rho_tonne_mm3:<8.2E}")
            lines.append("$")

            # Write PCOMP card - NASTRAN 2017 compatible format
            lines.append("$ Composite Property Card (PCOMP)")
            lines.append(f"$ Laminate: {material_object.name}")
            # PCOMP format for NASTRAN 2017: PCOMP PID Z0 NSM SB FT TREF GE LAM +
            # NASTRAN 2017 requires: simple continuation (+1, +2), proper field counts
            pid = 1
            # 8-character fixed field format (9 fields + continuation = 80 chars)
            lines.append(f"PCOMP   {pid:<8}                                                        +1")

            # Write continuation cards with ply data - NASTRAN 2017 format
            # Continuation format: +1, +2, +3... (simple numbering)
            # Each line: continuation_marker(8) + 2 plies max (8 fields) + next_continuation(8)
            # Format per ply: MID(8) T(8) THETA(8) SOUT(8)

            cont_num = 1
            ply_count = 0
            ply_line = f"+{cont_num:<7}"  # +1, +2, etc (8 chars total with padding)

            for i, lamina in enumerate(material_object.laminas):
                mat_name = lamina.material.name
                mid = unique_materials[mat_name][0]
                thickness_mm = lamina.thickness  # Already in mm
                theta = lamina.orientation

                # Add ply data: MID T THETA SOUT (each field 8 chars)
                ply_line += f"{mid:<8}{thickness_mm:<8.4f}{theta:<8.1f}{'':8}"
                ply_count += 1

                # Two plies per line max (2 plies = 8 fields)
                if ply_count == 2 and (i + 1) < len(material_object.laminas):
                    # Add continuation marker and write line
                    cont_num += 1
                    ply_line += f"+{cont_num:<7}"
                    lines.append(ply_line)
                    ply_line = f"+{cont_num:<7}"
                    ply_count = 0

            # Write final line if there's remaining data
            if ply_count > 0:
                lines.append(ply_line)
            lines.append("$")

        else:
            # Isotropic material - MAT1 and PSHELL
            # Calculate shear modulus if not provided
            if material.shear_modulus is None:
                G = material.youngs_modulus / (2 * (1 + material.poissons_ratio))
            else:
                G = material.shear_modulus

            lines.append("$ Material Properties (NASTRAN mm-tonne-s-N system)")
            # MAT1: MID E G NU RHO A TREF GE
            # CRITICAL: Must use proper 8-character fixed field format
            # Units: E (MPa=N/mm²), G (MPa), NU (dimensionless), RHO (tonne/mm³)
            # Match format from working examples: "73100.  " style (note: single decimal point)

            # Format E and G - use format with single decimal point and spaces
            # .1f already includes decimal point, so don't add another
            E_str = f"{material.youngs_modulus:.1f}"
            E_field = f"{E_str:<8.8}"  # Left-align, pad to 8 chars

            G_str = f"{G:.1f}"
            G_field = f"{G_str:<8.8}"

            # Poisson's ratio as .XX format
            nu_str = f".{int(material.poissons_ratio*100):02d}"
            nu_field = f"{nu_str:<8.8}"

            # Density in scientific notation (space before to match working format)
            # NOTE: MaterialConfig.density is already in tonne/mm³ (NASTRAN mm-tonne-s-N system)
            rho_str = f"{material.density:.2E}"
            # Ensure proper spacing - add space before if needed
            rho_field = f" {rho_str}" if len(rho_str) == 7 else rho_str
            rho_field = f"{rho_field:<8.8}"

            # Thermal expansion coefficient
            A_str = f"{2.1E-05:.1E}"
            A_field = f" {A_str}" if len(A_str) == 7 else A_str
            A_field = f"{A_field:<8.8}"

            mat1_line = f"MAT1    1       {E_field}{G_field}{nu_field}{rho_field}{A_field}"
            lines.append(mat1_line)
            lines.append("$")

            # Shell property
            lines.append("$ Shell Property")
            # PSHELL format: PID MID1 T MID2 12I/T^3 MID3 TS/T NSM Z1 Z2
            # Field positions: 1-8, 9-16, 17-24, 25-32, 33-40, ...
            # CRITICAL FIX v2.10.1: MID2 MUST BE SPECIFIED for homogeneous isotropic plates!
            # If MID2 is BLANK → NASTRAN treats element as MEMBRANE-ONLY (no bending stiffness)
            # For homogeneous plates: MID2 = MID1 (both reference the same MAT1 card)
            # Validated against NASTRAN Quick Reference Guide and Dowell theory:
            #   - Expected f₁ = 73.22 Hz for SSSS 500x400x3mm Al 6061-T6
            #   - With MID2=blank: Got f₁ = 21.86 Hz (3.35× too low, no bending!)
            #   - With MID2=1: Correct bending behavior (if density is correct)
            # Previous error (f₁ = 2.37 Hz with MID2=1) was due to 1000× density error in MAT1
            t_str = f"{panel.thickness:.4f}"
            lines.append(f"PSHELL  1       1       {t_str:<8}1       ")
            lines.append("$")

        # Grid points
        lines.append("$ Grid Points")
        grid_id = 1
        dx = panel.length / panel.nx
        dy = panel.width / panel.ny

        for j in range(panel.ny + 1):
            for i in range(panel.nx + 1):
                x = i * dx
                y = j * dy
                z = 0.0
                lines.append(f"GRID    {grid_id:<8}        {x:<8.1f}{y:<8.1f}{z:<8.1f}")
                grid_id += 1
        lines.append("$")

        # Elements
        lines.append("$ Elements")
        elem_id = 1
        for j in range(panel.ny):
            for i in range(panel.nx):
                n1 = j * (panel.nx + 1) + i + 1
                n2 = n1 + 1
                n3 = n1 + panel.nx + 2
                n4 = n1 + panel.nx + 1
                lines.append(f"CQUAD4  {elem_id:<8}{panel.property_id:<8}{n1:<8}{n2:<8}{n3:<8}{n4:<8}")
                elem_id += 1
        lines.append("$")

        # Boundary conditions
        lines.append("$ Boundary Conditions")
        # Handle both string and Enum types
        if hasattr(boundary_conditions, 'value'):
            bc_str = boundary_conditions.value
        else:
            bc_str = str(boundary_conditions)

        # Calculate total nodes
        total_nodes = (panel.nx + 1) * (panel.ny + 1)

        if bc_str.upper() == "SSSS":
            # Simply supported - constrain Z displacement on all edges
            lines.append("$ SSSS: Simply Supported on all four edges")
            edge_nodes = []

            # Bottom edge (j=0)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Top edge (j=ny)
            for i in range(panel.nx + 1):
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            # Left edge (i=0) - skip corners
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx) - skip corners
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            # Remove duplicates and sort
            edge_nodes = sorted(set(edge_nodes))

            # Write a single SPC1 card with continuation
            spc_line = "SPC1    1       3       "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "  # Continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "CCCC":
            # Clamped - constrain all translations and rotations on all edges
            lines.append("$ CCCC: Clamped on all four edges")
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

            # Write SPC1 card constraining all DOFs (123456) on edge nodes
            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "  # Continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "CFFF":
            # Cantilever - clamped at x=0, free elsewhere
            lines.append("$ CFFF: Clamped at x=0 (left edge), Free-Free-Free on other edges")
            left_edge_nodes = []

            # Left edge only (i=0, all j)
            for j in range(panel.ny + 1):
                left_edge_nodes.append(j * (panel.nx + 1) + 1)

            # Write SPC1 card constraining all DOFs on left edge
            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(left_edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "  # Continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "CFCF":
            # Clamped-Free-Clamped-Free: clamped at x=0 and x=length, free at y=0 and y=width
            lines.append("$ CFCF: Clamped at x=0 and x=L, Free at y=0 and y=W")
            edge_nodes = []

            # Left edge (i=0, all j)
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx, all j)
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            # Remove duplicates and sort
            edge_nodes = sorted(set(edge_nodes))

            # Write SPC1 card constraining all DOFs on clamped edges
            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "  # Continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "SCSC":
            # Simply supported-Clamped-Simply supported-Clamped
            lines.append("$ SCSC: Simply Supported at x=0 and x=L, Clamped at y=0 and y=W")

            # Left and right edges: Simply supported (DOF 3 only)
            ss_edge_nodes = []
            for j in range(panel.ny + 1):
                ss_edge_nodes.append(j * (panel.nx + 1) + 1)  # Left edge
                ss_edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)  # Right edge
            ss_edge_nodes = sorted(set(ss_edge_nodes))

            spc_line = "SPC1    1       3       "
            for i, node in enumerate(ss_edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "  # Continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

            # Bottom and top edges: Clamped (DOF 123456) - excluding corners already constrained
            c_edge_nodes = []
            for i in range(1, panel.nx):  # Skip corners to avoid double constraint
                c_edge_nodes.append(i + 1)  # Bottom edge
                c_edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)  # Top edge

            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(c_edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "  # Continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "SFSF":
            # Simply supported on two opposite edges (left/right), free on top/bottom
            lines.append("$ SFSF: Simply Supported at x=0 and x=L, Free at y=0 and y=W")
            edge_nodes = []

            # Left edge (i=0, all j)
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx, all j)
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            edge_nodes = sorted(set(edge_nodes))

            # Constrain DOF 3 (out-of-plane displacement) only
            spc_line = "SPC1    1       3       "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "FSFS":
            # Free on two opposite edges (left/right), simply supported on top/bottom
            lines.append("$ FSFS: Free at x=0 and x=L, Simply Supported at y=0 and y=W")
            edge_nodes = []

            # Bottom edge (j=0, all i)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Top edge (j=ny, all i)
            for i in range(panel.nx + 1):
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            edge_nodes = sorted(set(edge_nodes))

            # Constrain DOF 3 only
            spc_line = "SPC1    1       3       "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "CSCS":
            # Clamped-Simply supported-Clamped-Simply supported
            lines.append("$ CSCS: Clamped at x=0 and x=L, Simply Supported at y=0 and y=W")

            # Left and right edges: Clamped (all DOFs)
            c_edge_nodes = []
            for j in range(panel.ny + 1):
                c_edge_nodes.append(j * (panel.nx + 1) + 1)  # Left edge
                c_edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)  # Right edge
            c_edge_nodes = sorted(set(c_edge_nodes))

            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(c_edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

            # Bottom and top edges: Simply supported (DOF 3 only)
            ss_edge_nodes = []
            for i in range(1, panel.nx):  # Skip corners to avoid double constraint
                ss_edge_nodes.append(i + 1)  # Bottom edge
                ss_edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)  # Top edge

            spc_line = "SPC1    1       3       "
            for i, node in enumerate(ss_edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "FFFF":
            # Free-free on all edges (space structures, no attachment)
            lines.append("$ FFFF: Free on all four edges (space structure)")
            lines.append("$ No edge constraints - rigid body modes will be present")
            # No edge constraints needed
            # NASTRAN will handle rigid body modes in modal analysis

        elif bc_str.upper() == "CCCF":
            # Three edges clamped, top edge free
            lines.append("$ CCCF: Clamped at x=0, x=L, y=0; Free at y=W (top)")
            edge_nodes = []

            # Bottom edge (j=0, all i)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Left edge (i=0, all j except top corner)
            for j in range(panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx, all j except top corner)
            for j in range(panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            edge_nodes = sorted(set(edge_nodes))

            # Clamp all these edges (all DOFs)
            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "SSSF":
            # Three edges simply supported, top edge free
            lines.append("$ SSSF: Simply Supported at x=0, x=L, y=0; Free at y=W (top)")
            edge_nodes = []

            # Bottom edge (j=0, all i)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Left edge (i=0, all j except top corner)
            for j in range(panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx, all j except top corner)
            for j in range(panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            edge_nodes = sorted(set(edge_nodes))

            # Simply support (DOF 3 only)
            spc_line = "SPC1    1       3       "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        elif bc_str.upper() == "FCFC":
            # Free at left/right edges, clamped at top/bottom
            lines.append("$ FCFC: Free at x=0 and x=L, Clamped at y=0 and y=W")
            edge_nodes = []

            # Bottom edge (j=0, all i)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Top edge (j=ny, all i)
            for i in range(panel.nx + 1):
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            edge_nodes = sorted(set(edge_nodes))

            # Clamp (all DOFs)
            spc_line = "SPC1    1       123456  "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        else:
            # Unknown boundary condition - default to SSSS with warning
            lines.append(f"$ WARNING: Unknown boundary condition '{bc_str}' - defaulting to SSSS")
            lines.append("$ SSSS: Simply Supported on all four edges")
            edge_nodes = []

            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            edge_nodes = sorted(set(edge_nodes))

            spc_line = "SPC1    1       3       "
            for i, node in enumerate(edge_nodes):
                if i > 0 and i % 6 == 0:
                    lines.append(spc_line)
                    spc_line = "+       "
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)

        # Add constraints to prevent in-plane rigid body modes (per MSC Nastran reference)
        # Constrain X translation at corner node 1 to prevent X rigid body translation
        lines.append("SPC1    1       1       1")

        # Constrain Y translation at TWO corners (nodes 1 and last node) to prevent
        # Y rigid body translation AND in-plane rotation about Z-axis
        lines.append(f"SPC1    1       2       1       {total_nodes}")

        # CRITICAL FIX v2.7.0: DO NOT constrain DOF 6 (Rz drilling rotation) on all nodes!
        # Previous code constrained Rz on ALL nodes, preventing plate bending/twisting
        # This caused 3.4× frequency error and zero aeroelastic coupling
        # Solution: Let NASTRAN handle drilling DOF with AUTOSPC or use K6ROT parameter
        # Constraining Rz on all nodes is equivalent to making the plate rigid in torsion
        # For thin plates, Rz constraints should be minimal or handled by solver automatically
        lines.append("$")
        lines.append("$ NOTE: DOF 6 (drilling rotation) NOT constrained")
        lines.append("$ NASTRAN will use PARAM,AUTOSPC to handle any singularities")
        lines.append("$")

        # Eigenvalue extraction
        lines.append("$ Eigenvalue Extraction")
        sid = 1
        msglvl = 0  # Set to 0 to avoid MSGLVL:10 <= 4 error
        # Using EIGRL (Lanczos) for now - more reliable with fixed-field format
        lines.append(f"EIGRL   {sid:8d}{'':16}{n_modes:8d}{msglvl:8d}")
        lines.append("$")

        # Aerodynamic reference - VALIDATED FORMAT
        lines.append("$ Aerodynamic Reference")
        lines.append("$ AERO: ACSID VELOCITY REFC RHOREF")
        lines.append("$   ACSID=0: Basic coordinate system")
        lines.append("$   VELOCITY=1.0: Reference velocity (actual velocities in FLFACT)")
        lines.append(f"$   REFC={panel.length:.1f}: Reference chord length (mm)")
        lines.append(f"$   RHOREF: Reference density (tonne/mm³ = kg/m³ × 1e-12)")
        # AERO card with correct air density in tonne/mm³
        # Format: AERO ACSID VELOCITY REFC RHOREF
        # Use compact NASTRAN scientific notation (e.g., 1.225-12 instead of 1.225E-12)
        import math
        if aero.reference_density != 0:
            exponent = int(math.floor(math.log10(abs(aero.reference_density))))
            mantissa = aero.reference_density / (10 ** exponent)
            # Format as: mantissa+exponent or mantissa-exponent (8 chars max)
            rho_str = f"{mantissa:.3f}{exponent:+d}"  # e.g., "1.225-9"

            # CRITICAL FIX v2.1.9: Validate field width (NASTRAN limit: 8 characters)
            if len(rho_str) > 8:
                logger.warning(f"Density compact notation '{rho_str}' exceeds 8 chars, using E-notation")
                # Fallback to standard E-notation
                rho_str = f"{aero.reference_density:.3E}"
                # If still too long, reduce precision
                if len(rho_str) > 8:
                    rho_str = f"{aero.reference_density:.2E}"
                # Ensure it fits by truncation as last resort
                rho_str = rho_str[:8]
                logger.info(f"Density field: '{rho_str}' (truncated to 8 chars)")

            # Log the actual density for verification
            rho_kg_m3 = aero.reference_density * 1e9  # Convert back to kg/m³ for readability
            lines.append(f"$ Reference density: {rho_kg_m3:.4f} kg/m³ (altitude: {aero.altitude}m)")
        else:
            rho_str = "0.0"
        lines.append(f"AERO    0       1.      {panel.length:<8.1f}{rho_str:<8s}")
        lines.append("$")

        # AERODYNAMIC MODEL - Select based on Mach number
        # Determine aerodynamic theory based on user selection or Mach number
        # User selection takes priority, otherwise use Mach-based logic
        # CRITICAL v2.1.9: Enhanced logging to trace user selection
        logger.info(f"=== BDF GENERATOR: AERODYNAMIC THEORY ===")
        logger.info(f"aerodynamic_theory parameter: {aerodynamic_theory}")
        logger.info(f"Mach number: {aero.mach_number}")

        if aerodynamic_theory:
            # Explicit user choice
            use_piston_theory = (aerodynamic_theory == "PISTON_THEORY")
            logger.info(f"✓ USER SELECTION: {'PISTON THEORY (CAERO5)' if use_piston_theory else 'DOUBLET LATTICE (CAERO1)'}")
        else:
            # CRITICAL FIX: Auto-select based on Mach number (industry standard)
            # DLM (Doublet Lattice): M < 1.5 (subsonic/transonic)
            # Piston Theory: M >= 1.5 (supersonic)
            use_piston_theory = (aero.mach_number >= 1.5)
            logger.info(f"AUTO-SELECT: {'PISTON THEORY (CAERO5)' if use_piston_theory else 'DOUBLET LATTICE (CAERO1)'} for M={aero.mach_number}")

        logger.info(f"=========================================")

        if use_piston_theory:
            # CAERO5 - Piston Theory for supersonic flow (M >= 1.5)
            lines.append("$ Piston Theory (CAERO5) - Supersonic Aerodynamics")
            lines.append("$ Reference: MSC Nastran Aeroelastic Analysis User's Guide, Example HA145HA")
            lines.append("$")

            # AEFACT 10 - Thickness integrals for piston theory (flat panel = all zeros)
            lines.append("$ Thickness Integrals (I1-I6) - flat panel")
            lines.append(f"AEFACT  {10:<8}{0.0:<8}{0.0:<8}{0.0:<8}{0.0:<8}{0.0:<8}{0.0:<8}")
            lines.append("$")

            # AEFACT 20 - Mach-Alpha array for PAERO5
            # CRITICAL: NASTRAN Error 6171 if wrong count, Error 6185 if Mach not in range
            # Format: Mach_min, alpha_min, Mach_max, alpha_max
            # NASTRAN will interpolate for Mach numbers in [Mach_min, Mach_max]
            # For piston theory, use Mach_max=3.0 to cover typical supersonic range
            lines.append("$ PAERO5 Mach-Alpha Array (LALPHA reference)")
            lines.append(f"AEFACT  {20:<8}{aero.mach_number:<8.2f}{0.0:<8}{3.0:<8.2f}{0.0:<8}")
            lines.append("$")

            # PAERO5 - Piston Theory Property (REQUIRED with two continuation lines)
            # Format from MSC Nastran Example HA145HA (Listing 8-30)
            lines.append("$ Piston Theory Property")
            pid_aero = 1001
            nalpha = 1  # Number of alpha values
            lalpha = 20  # AEFACT ID for alpha values
            # Main card: PAERO5, PID, NALPHA, LALPHA, blank fields, then continuation in field 10 (position 72)
            # Fields: 1=PAERO5, 2=PID, 3=NALPHA, 4=LALPHA, 5-9=blank (40 chars), 10=continuation
            lines.append(f"PAERO5  {pid_aero:<8}{nalpha:<8}{lalpha:<8}{'':40}+PA5")
            # CRITICAL FIX v2.15.1: Number of CAOC values MUST equal NTHICK from CAERO5!
            # NASTRAN Error 6172: "NUMBER OF CAOCI ENTRIES MUST EQUAL THE NUMBER OF STRIPS"
            # NTHICK = 10, so PAERO5 must have exactly 10 CAOC values (not 16!)
            # First continuation (+PA5): CAOC1-CAOC8 (control surface corrections, zeros for flat panel)
            lines.append(f"+PA5    {0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}+PA51")
            # Second continuation (+PA51): CAOC9-CAOC10 (remaining 2 values to reach NTHICK=10)
            lines.append(f"+PA51   {0.0:<8.1f}{0.0:<8.1f}")
            lines.append("$")

            # CRITICAL FIX v2.14.5: SINGLE CAERO5 card for panel (industry standard)
            # Previous implementation used 10 non-contiguous CAERO5 cards which caused:
            #   1. Non-standard NASTRAN practice
            #   2. SPLINE1 box numbering errors
            #   3. Aeroelastic coupling failures
            # Reference: MSC NASTRAN Aeroelastic Analysis User's Guide - one CAERO5 per surface
            lines.append("$ PISTON THEORY PANEL (CAERO5)")
            lines.append("$ CRITICAL: Single CAERO5 card with NSPAN divisions (industry standard)")
            lines.append("$")

            # Single CAERO5 card parameters
            eid = 1001  # Element ID (contiguous boxes start from here)
            nspan = 10  # Spanwise divisions (creates 10 aerodynamic strips)
            lspan = 0  # AEFACT ID for spanwise spacing (0=blank=uniform)
            nthick = 10  # AEFACT ID for thickness integrals

            # CRITICAL FIX: Get piston theory order from aero config
            piston_order = getattr(aero, 'piston_theory_order', 1)
            logger.info(f">>> CAERO5 NTHRY field = {piston_order} (Piston Theory Order) <<<")

            # Panel geometry (FULL PANEL, not strips)
            # Point 1 (root leading edge): (0, 0, 0)
            # Point 2 (root trailing edge): (chord, 0, 0) - specified by X12
            # Point 4 (tip leading edge): (0, span, 0)
            # Point 3 (tip trailing edge): (chord, span, 0) - specified by X43
            x1, y1, z1 = 0.0, 0.0, 0.0  # Root leading edge
            x12 = panel.length  # Chord length at root
            x4, y4, z4 = 0.0, panel.width, 0.0  # Tip leading edge (span direction)
            x43 = panel.length  # Chord length at tip (rectangular panel)

            # CAERO5 main card with CRITICAL NTHRY field
            # Format: CAERO5 EID PID CP NSPAN LSPAN NTHRY NTHICK blank +continuation
            # Field positions: 1-8, 9-16, 17-24, 25-32, 33-40, 41-48, 49-56, 57-64, 65-72, 73-80
            lines.append(f"CAERO5  {eid:<8}{pid_aero:<8}        {nspan:<8}{'':8}{piston_order:<8}{nthick:<8}{'':8}+CA5")
            #                 ^EID    ^PID     ^CP      ^NSPAN   ^LSPAN   ^NTHRY      ^NTHICK  ^blank  ^cont
            #                                  (blank)           (ORDER!)

            # Continuation: X1, Y1, Z1, X12, X4, Y4, Z4, X43
            lines.append(f"+CA5    {x1:<8.1f}{y1:<8.1f}{z1:<8.1f}{x12:<8.1f}{x4:<8.1f}{y4:<8.1f}{z4:<8.1f}{x43:<8.1f}")
            lines.append("$")
            lines.append(f"$ CAERO5 creates boxes {eid} through {eid + nspan - 1} (10 contiguous boxes)")
            lines.append("$")

            # CRITICAL FIX v2.14.5: SINGLE SPLINE1 for single CAERO5 with CORRECT box numbering
            # Previous implementation created 10 SPLINE1 cards referencing non-existent boxes
            # Now: ONE SPLINE1 card referencing contiguous boxes 1001-1010
            lines.append("$ SPLINE - SURFACE INTERPOLATION")
            lines.append("$ CRITICAL: Single SPLINE1 for single CAERO5 (correct box numbering)")
            setg_id = 1  # SET1 with all structural grids

            # Box numbering for single CAERO5:
            # - Boxes are numbered starting at EID (1001)
            # - NSPAN divisions create NSPAN boxes
            # - Box IDs: 1001, 1002, 1003, ..., 1010 (contiguous!)
            spline_id = 1
            box1 = eid  # First box = EID = 1001
            box2 = eid + nspan - 1  # Last box = 1001 + 10 - 1 = 1010

            lines.append(f"SPLINE1 {spline_id:<8}{eid:<8}{box1:<8}{box2:<8}{setg_id:<8}")

            # SET1 - All structural grid points
            lines.append(f"SET1    {setg_id:<8}{1:<8}THRU    {(panel.nx + 1) * (panel.ny + 1)}")
            lines.append("$")

        else:
            # CAERO1 - Doublet Lattice Method for subsonic/transonic (M < 1.5)
            lines.append("$ Doublet Lattice Method (CAERO1) - Subsonic/Transonic")
            lines.append("$")

            lines.append("$ Doublet Lattice Method Property")
            lines.append("PAERO1  1")
            lines.append("$")

            # CAERO1 card for doublet lattice method - CORRECTED GEOMETRY
            lines.append("$ Doublet Lattice Method Panel")
            # CAERO1 format: EID PID CP NSPAN NCHORD LSPAN LCHORD IGD
            # Use minimum 8x8 mesh for adequate flutter resolution (per NASA TP-2000-209136)
            aero_nx = max(8, panel.nx // 2)  # Minimum 8 spanwise panels, or half structural mesh
            aero_ny = max(8, panel.ny // 2)  # Minimum 8 chordwise panels, or half structural mesh
            lines.append(f"CAERO1  {1:<8}{1:<8}        {aero_nx:<8}{aero_ny:<8}                1       +CA1")
            # Continuation: X1, Y1, Z1, X12, X4, Y4, Z4, X43 (all 8-char fields)
            # CRITICAL FIX: X43 should be chord length, not X-coordinate
            # Geometry: Point 1 at (0,0,0), Point 2 at (X12,0,0), Point 4 at (0,Y4,0), Point 3 at (X12,Y4,0)
            x1, y1, z1 = 0.0, 0.0, 0.0
            x12 = panel.length  # Chord length (root)
            x4, y4, z4 = 0.0, panel.width, 0.0  # Leading edge at span
            x43 = panel.length  # Chord length (tip) - CORRECTED
            lines.append(f"+CA1    {x1:<8.1f}{y1:<8.1f}{z1:<8.1f}{x12:<8.1f}{x4:<8.1f}{y4:<8.1f}{z4:<8.1f}{x43:<8.1f}")
            lines.append("$")

            # SPLINE1 for surface interpolation - MUCH MORE ROBUST
            lines.append("$ Spline - Surface Interpolation")
            # SPLINE1: EID CAERO BOX1 BOX2 SETG DZ METH USAGE NELEM MELIN
            # Critical: BOX1 and BOX2 define the aerodynamic box range
            # For CAERO1 with EID=1, boxes are numbered 1 to (NSPAN*NCHORD)
            aero_panels = aero_nx * aero_ny
            box1 = 1  # First aerodynamic box
            box2 = aero_panels  # Last aerodynamic box
            setg_id = 1  # SET1 containing all structural grids
            # DZ = 0.0 means no offset, METH blank uses default (IPS method)
            lines.append(f"SPLINE1 {1:<8}{1:<8}{box1:<8}{box2:<8}{setg_id:<8}")
            # SET1: Define all structural grid points for interpolation
            total_grids = (panel.nx + 1) * (panel.ny + 1)
            lines.append(f"SET1    {setg_id:<8}{1:<8}THRU    {total_grids:<8}")
            lines.append("$")

        # Flutter cards
        lines.append("$ Flutter Analysis")
        # CRITICAL: Add structural damping table (TABDMP1) for realistic flutter analysis
        # Without damping, NASTRAN reports zero damping at all speeds (unrealistic)
        # Typical aerospace structures: 2-5% critical damping (g = 0.02 to 0.05)
        lines.append("$ Structural Damping Table (frequency-dependent)")
        # TABDMP1 format: Line 1: TABDMP1 TID TYPE
        #                 Line 2+: f1 g1 f2 g2 ... ENDT
        # TYPE = CRIT for critical damping ratio (g), G for structural damping coefficient
        lines.append("TABDMP1 1       CRIT")
        # Frequency (Hz) and damping pairs: constant 3% critical damping (0.03) from 0-1000 Hz
        lines.append("+       0.0     0.03    1000.0  0.03    ENDT")
        lines.append("$")

        # FLUTTER card: PK method with density (1), Mach (2), reduced freq/velocity (3)
        lines.append("FLUTTER 1       PK      1       2       3       L")

        # CRITICAL FIX v2.13.0: Density ratio depends on aerodynamic theory
        # For PISTON THEORY (supersonic): density_ratio = 1.0 (one-sided pressure already in theory)
        # For DLM (subsonic): density_ratio = 0.5 (symmetric flow on both sides)
        if use_piston_theory:
            lines.append("FLFACT  1       1.0")  # Piston theory: full density ratio
        else:
            lines.append("FLFACT  1       0.5")  # DLM: half density ratio for symmetric flow

        # Mach number (FLFACT 2) - use exact Mach number, not rounded
        # CRITICAL FIX v2.13.0: Use .2f instead of .1f to preserve precision (1.27 not 1.3)
        if use_piston_theory:
            # For supersonic, use specified Mach only (removed extra M=3.0)
            lines.append(f"FLFACT  2       {aero.mach_number:.2f}")
        else:
            # For subsonic/transonic, use specified Mach number
            lines.append(f"FLFACT  2       {aero.mach_number:.2f}")

        # For PK method, FLFACT 3 contains velocities
        if aero.velocities:
            # Write velocities in multiple lines if needed
            vel_idx = 0
            line_count = 0
            while vel_idx < len(aero.velocities):
                if line_count == 0:
                    vel_line = "FLFACT  3       "
                else:
                    # NASTRAN continuation line - starts with continuation marker
                    vel_line = "+FL3    "  # Exactly 8 characters for continuation marker

                # NASTRAN fixed format: 80 chars max, columns 73-80 for continuation
                # First line: FLFACT+ID (16 chars) + velocities (max 56 chars = 7 velocities) + cont (8 chars) = 80
                # Continuation: marker (8 chars) + velocities (max 64 chars = 8 velocities) = 72 chars
                max_velocities = 7 if line_count == 0 else 8  # First line has LESS space due to header
                for i in range(max_velocities):
                    if vel_idx < len(aero.velocities):
                        vel = aero.velocities[vel_idx]
                        # Format for 8-character field
                        if vel >= 1e7:
                            vel_str = f"{vel:.1e}".ljust(8)
                        elif vel >= 1e6:
                            vel_str = f"{vel/1e6:.2f}+6".ljust(8)
                        else:
                            vel_str = f"{vel:.0f}.".ljust(8)
                        vel_line += vel_str
                        vel_idx += 1
                    else:
                        break

                # Add continuation marker at end of line if more velocities follow
                if vel_idx < len(aero.velocities):
                    # Pad to position 72, then add 8-char continuation marker in columns 73-80
                    vel_line = vel_line.ljust(72) + "+FL3    "

                lines.append(vel_line)
                line_count += 1
        else:
            # Extended default velocity range: 100-2500 m/s (100,000-2,500,000 mm/s)
            # Per MIL-A-8870C: Must extend at least 15% beyond predicted flutter speed
            # Using logarithmic spacing for better resolution near flutter boundary
            lines.append("$ Extended velocity range: 100-2500 m/s for comprehensive flutter envelope")
            lines.append("FLFACT  3       1.0E+05 2.0E+05 3.0E+05 4.0E+05 5.0E+05 6.0E+05 7.0E+05 ".ljust(72) + "+FL3    ")
            lines.append("+FL3    8.0E+05 9.0E+05 1.0E+06 1.2E+06 1.4E+06 1.6E+06 1.8E+06 ".ljust(72) + "+FL31   ")
            lines.append("+FL31   2.0E+06 2.2E+06 2.5E+06")
        lines.append("$")

        # Aerodynamic matrices - select based on aerodynamic method
        # CRITICAL FIX v2.14.0: Use exact Mach number (.2f not .1f)!
        if use_piston_theory:
            # MKAERO1 for piston theory (CAERO5) - Reference uses MKAERO1, not MKAERO2
            lines.append("$ Aerodynamic Matrices - Piston Theory (MKAERO1)")
            # Include both specified Mach and M=3.0 for interpolation
            lines.append(f"MKAERO1 {aero.mach_number:<8.2f}{3.0:<8.1f}{'':48}+MK1     ")
            # Continuation card with validated reduced frequencies (MUST have leading zeros)
            lines.append("+MK1    0.001   0.1     0.2     0.4")
            lines.append("$")
        else:
            # MKAERO1 for doublet lattice (CAERO1)
            lines.append("$ Aerodynamic Matrices - Doublet Lattice (MKAERO1)")
            # Main card with Mach number only
            lines.append(f"MKAERO1 {aero.mach_number:<8.2f}{'':56}+MK1     ")
            # Continuation card with validated reduced frequencies (MUST have leading zeros)
            lines.append("+MK1    0.001   0.1     0.2     0.4")
            lines.append("$")

        # End of data
        lines.append("ENDDATA")

        # Write file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

        logger.info(f"Generated corrected SOL145 BDF file: {filepath}")
        return str(filepath)


def create_sol145_flutter_bdf(config: Dict[str, Any], output_dir: str = ".") -> str:
    """Create a SOL145 flutter analysis BDF file with corrected piston theory cards"""

    generator = Sol145BDFGenerator(output_dir)

    # Extract panel config
    panel = PanelConfig(
        length=config.get('panel_length', 1000.0),  # mm
        width=config.get('panel_width', 800.0),      # mm
        thickness=config.get('thickness', 2.0),       # mm
        nx=config.get('nx', 10),
        ny=config.get('ny', 10)
    )

    # Extract material config (NASTRAN units: mm-tonne-s-N)
    material = MaterialConfig(
        youngs_modulus=config.get('youngs_modulus', 71700.0),  # MPa (N/mm^2)
        poissons_ratio=config.get('poissons_ratio', 0.33),
        density=config.get('density', 2.81e-12)  # tonne/mm^3 (Mg/mm^3) - NASTRAN uses tonne, not kg!
    )

    # Extract aero config
    # Calculate proper air density at altitude using ISA atmosphere model
    altitude = config.get('altitude', 10000)  # meters
    # ISA atmosphere model: ρ = ρ₀ × exp(-altitude/H) where H ≈ 8500m (scale height)
    # Reference: U.S. Standard Atmosphere 1976
    rho_sea_level_kg_m3 = 1.225  # kg/m³ at sea level, 15°C

    # More accurate ISA model for troposphere (altitude < 11000m)
    if altitude <= 11000:
        # Temperature lapse rate: -6.5°C/km
        T0 = 288.15  # Sea level temperature (K)
        T = T0 - 0.0065 * altitude  # Temperature at altitude (K)
        rho_at_alt_kg_m3 = rho_sea_level_kg_m3 * ((T / T0) ** 4.2561)
    else:
        # Stratosphere (constant temperature -56.5°C)
        # Use exponential decay approximation
        rho_at_alt_kg_m3 = rho_sea_level_kg_m3 * (2.71828 ** (-altitude / 8500.0))

    # CRITICAL FIX: Use 1e-12 for tonne/mm³ (consistent with MaterialConfig.density)
    # Previous bug used 1e-9 (kg/mm³) which caused 1000x density ratio error
    rho_at_alt_tonne_mm3 = rho_at_alt_kg_m3 * 1e-12  # Convert kg/m³ to tonne/mm³
    logger.info(f"ISA atmosphere at {altitude}m: rho = {rho_at_alt_kg_m3:.4f} kg/m^3")

    aero = AeroConfig(
        mach_number=config.get('mach_number', 3.0),
        reference_velocity=config.get('velocity', 1.0e6),  # mm/s
        reference_chord=config.get('panel_length', 1000.0),  # mm
        reference_density=rho_at_alt_tonne_mm3,  # tonne/mm³ at specified altitude
        altitude=altitude,
        reduced_frequencies=config.get('reduced_frequencies', [0.0, 0.001, 0.01, 0.1, 0.2]),
        velocities=config.get('velocities')  # mm/s
    )

    # Generate BDF
    return generator.generate_bdf(
        panel=panel,
        material=material,
        aero=aero,
        boundary_conditions=config.get('boundary_conditions', 'SSSS'),
        n_modes=config.get('n_modes', 10),
        output_filename=config.get('output_filename', 'flutter_sol145.bdf')
    )