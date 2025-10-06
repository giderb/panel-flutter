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


@dataclass
class MaterialConfig:
    """Material properties for BDF (SI units: mm-kg-s-N)"""
    youngs_modulus: float  # MPa (N/mm^2)
    poissons_ratio: float  # dimensionless
    density: float  # kg/mm^3 = original_kg_per_m3 * 1e-9
    shear_modulus: Optional[float] = None  # MPa (N/mm^2)
    material_id: int = 1


@dataclass
class AeroConfig:
    """Aerodynamic configuration for BDF (SI units: mm-kg-s-N)"""
    mach_number: float
    reference_velocity: float  # mm/s
    reference_chord: float  # mm
    reference_density: float  # kg/mm^3
    reduced_frequencies: List[float] = None
    velocities: List[float] = None  # mm/s


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
        aerodynamic_theory: Optional[str] = None
    ) -> str:
        """Generate a NASTRAN BDF file for SOL145 flutter analysis with correct cards"""

        filepath = self.output_dir / output_filename
        lines = []

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
        # PARAM VREF for velocity conversion (if velocities in in/s, converts to ft/s for output)
        lines.append("PARAM   VREF    1.0")  # Will be adjusted based on unit system
        lines.append("$")

        # Material - VALIDATED FORMAT
        # Calculate shear modulus if not provided
        if material.shear_modulus is None:
            G = material.youngs_modulus / (2 * (1 + material.poissons_ratio))
        else:
            G = material.shear_modulus

        lines.append("$ Material Properties (SI units in mm)")
        # MAT1: MID E G NU RHO A TREF GE
        # CRITICAL: Must have proper spacing between all fields
        lines.append(f"MAT1    1       {material.youngs_modulus:.0f}.  {G:.0f}.  .{material.poissons_ratio*100:.0f}     {material.density:.2E} {2.1E-05:.1E}")
        lines.append("$")

        # Shell property
        lines.append("$ Shell Property")
        # Use sufficient precision for thin panels
        lines.append(f"PSHELL  1       1       {panel.thickness:.4f}")
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
        lines.append("$ Boundary Conditions (Simply Supported)")
        # Handle both string and Enum types
        if hasattr(boundary_conditions, 'value'):
            bc_str = boundary_conditions.value
        else:
            bc_str = str(boundary_conditions)

        if bc_str.upper() == "SSSS":
            # Simply supported - constrain Z displacement on all edges
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

        # Calculate total nodes (needed for constraints below)
        total_nodes = (panel.nx + 1) * (panel.ny + 1)

        # Add constraints to prevent in-plane rigid body modes (per MSC Nastran reference)
        # Constrain X translation at corner node 1 to prevent X rigid body translation
        lines.append("SPC1    1       1       1")

        # Constrain Y translation at TWO corners (nodes 1 and last node) to prevent
        # Y rigid body translation AND in-plane rotation about Z-axis
        lines.append(f"SPC1    1       2       1       {total_nodes}")

        # Constrain drilling DOF (DOF 6) on ALL nodes
        # CRITICAL: CQUAD4 elements have zero stiffness for drilling rotation (rotation about Z)
        # Must constrain DOF 6 to prevent grid point singularities (per MSC Nastran reference)
        lines.append(f"SPC1    1       6       1       THRU    {total_nodes}")
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
        # AERO card matching validated working example
        lines.append(f"AERO    0       1.      {panel.length:<8.1f}1.225-12")
        lines.append("$")

        # AERODYNAMIC MODEL - Select based on Mach number
        # Determine aerodynamic theory based on user selection or Mach number
        # User selection takes priority, otherwise use Mach-based logic
        if aerodynamic_theory:
            # Explicit user choice
            use_piston_theory = (aerodynamic_theory == "PISTON_THEORY")
        else:
            # Auto-select based on Mach number: CAERO5 for M >= 1.5, CAERO1 for M < 1.5
            use_piston_theory = (aero.mach_number >= 1.5)

        if use_piston_theory:
            # CAERO5 - Piston Theory for supersonic flow (M >= 1.5)
            lines.append("$ Piston Theory (CAERO5) - Supersonic Aerodynamics")
            lines.append("$ Reference: MSC Nastran Aeroelastic Analysis User's Guide, Example HA145HA")
            lines.append("$")

            # AEFACT 10 - Thickness integrals for piston theory (flat panel = all zeros)
            lines.append("$ Thickness Integrals (I1-I6) - flat panel")
            lines.append(f"AEFACT  {10:<8}{0.0:<8}{0.0:<8}{0.0:<8}{0.0:<8}{0.0:<8}{0.0:<8}")
            lines.append("$")

            # AEFACT 20 for Mach/alpha combinations - Reference has M=2.0 and M=3.0
            lines.append("$ Mach and Alpha Combinations")
            lines.append(f"AEFACT  {20:<8}{aero.mach_number:<8.1f}{0.0:<8}{3.0:<8}{0.0:<8}")
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
            # First continuation: 8 CAOC values (control surface parameters, zeros for flat panel)
            lines.append(f"+PA5    {0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}+PA51")
            # Second continuation: 2 more CAOC values
            lines.append(f"+PA51   {0.0:<8.1f}{0.0:<8.1f}")
            lines.append("$")

            # CAERO5 - 10 separate panels following reference format
            # Reference: MSC Nastran Example HA145HA uses 10 CAERO5 cards (EID 1001-10001)
            lines.append("$ PISTON THEORY PANEL (CAERO5)")
            lines.append("$")

            nspan = 10  # Spanwise divisions per CAERO5 card
            lspan = 1  # AEFACT ID for spanwise spacing (optional, leave blank)
            nthick = 10  # AEFACT ID for thickness integrals

            # Panel geometry
            chord = panel.length
            strip_width = panel.width / 10  # Divide width into 10 strips

            # Generate 10 CAERO5 cards (EID 1001, 2001, 3001, ..., 10001)
            for strip in range(10):
                eid = 1001 + (strip * 1000)
                y_start = strip * strip_width
                y_end = (strip + 1) * strip_width

                # Each strip: point 1 at (0, y_start, 0), point 4 at (0, y_end, 0)
                x1, y1, z1 = 0.0, y_start, 0.0
                x12 = chord  # Chord length in x-direction
                x4, y4, z4 = 0.0, y_end, 0.0
                x43 = chord  # Chord length in x-direction

                # CAERO5 main card: EID, PID, CP, NSPAN, LSPAN, NTHRY, NTHICK, blank, continuation
                # Fields: 1=CAERO5, 2=EID, 3=PID, 4=CP, 5=NSPAN, 6=LSPAN, 7=NTHRY, 8=NTHICK, 9=blank, 10=continuation
                cont_marker = f"+CA{strip:02d}"
                lines.append(f"CAERO5  {eid:<8}{pid_aero:<8}        {nspan:<8}{'':8}        {nthick:<8}{'':8}{cont_marker}")
                # Continuation: X1, Y1, Z1, X12, X4, Y4, Z4, X43
                lines.append(f"+CA{strip:02d}   {x1:<8.1f}{y1:<8.1f}{z1:<8.1f}{x12:<8.1f}{x4:<8.1f}{y4:<8.1f}{z4:<8.1f}{x43:<8.1f}")

            lines.append("$")

            # SPLINE1 - Surface interpolation connecting aero panel to structural grids
            # Create separate SPLINE for each CAERO5 since box numbers are non-contiguous
            lines.append("$ SPLINE - SURFACE INTERPOLATION")
            setg_id = 1  # SET1 with all structural grids

            # Create one SPLINE for each CAERO5 card
            for strip in range(10):
                spline_id = strip + 1
                caero_eid = 1001 + (strip * 1000)
                box1 = caero_eid  # First box of this CAERO5
                box2 = caero_eid + (nspan - 1)  # Last box of this CAERO5

                lines.append(f"SPLINE1 {spline_id:<8}{caero_eid:<8}{box1:<8}{box2:<8}{setg_id:<8}")

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
            aero_nx = 4  # 4x4 aerodynamic mesh for better interpolation
            aero_ny = 4
            lines.append(f"CAERO1  {1:<8}{1:<8}        {aero_nx:<8}{aero_ny:<8}                1       +CA1")
            # Continuation: X1, Y1, Z1, X12, X4, Y4, Z4, X43 (all 8-char fields)
            lines.append(f"+CA1    {0.0:<8.1f}{0.0:<8.1f}{0.0:<8.1f}{panel.length:<8.1f}{0.0:<8.1f}{panel.width:<8.1f}{panel.length:<8.1f}{panel.width:<8.1f}")
            lines.append("$")

            # SPLINE1 for surface interpolation - MUCH MORE ROBUST
            lines.append("$ Spline - Surface Interpolation")
            aero_panels = aero_nx * aero_ny
            lines.append(f"SPLINE1 1       1       1       {aero_panels:<8}1")
            lines.append(f"SET1    1       1       THRU    {(panel.nx + 1) * (panel.ny + 1)}")
            lines.append("$")

        # Flutter cards
        lines.append("$ Flutter Analysis")
        # FLUTTER card: PK method with density (1), Mach (2), reduced freq/velocity (3)
        lines.append("FLUTTER 1       PK      1       2       3       L")

        # Density ratio list (FLFACT 1) - 0.5 for one-sided flow (air on one side only)
        lines.append("FLFACT  1       0.5")

        # Mach number (FLFACT 2) - include multiple Mach numbers for comprehensive analysis
        if use_piston_theory:
            # For supersonic, test both M=2.0 and M=3.0 as in reference case
            lines.append(f"FLFACT  2       {aero.mach_number:.1f}     3.0")
        else:
            # For subsonic/transonic, use same Mach number
            lines.append(f"FLFACT  2       {aero.mach_number:.1f}     {aero.mach_number:.1f}")

        # For PK method, FLFACT 3 contains velocities
        if aero.velocities:
            # Write velocities in multiple lines if needed
            vel_idx = 0
            while vel_idx < len(aero.velocities):
                if vel_idx == 0:
                    vel_line = "FLFACT  3       "
                else:
                    # NASTRAN continuation line - 8-character field for continuation marker
                    vel_line = "+       "  # Exactly 8 characters for continuation marker
                # Add up to 8 velocities per line (6 velocities for continuation lines)
                max_velocities = 8 if vel_idx == 0 else 6  # First line has more space
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
                lines.append(vel_line)
        else:
            # Default velocity range in mm/s
            lines.append("FLFACT  3       5.0E+05 6.0E+05 7.0E+05 8.0E+05 9.0E+05 1.0E+06 1.1E+06 1.2E+06")
            lines.append("+       1.3E+06 1.4E+06 1.5E+06")
        lines.append("$")

        # Aerodynamic matrices - select based on aerodynamic method
        if use_piston_theory:
            # MKAERO1 for piston theory (CAERO5) - Reference uses MKAERO1, not MKAERO2
            lines.append("$ Aerodynamic Matrices - Piston Theory (MKAERO1)")
            # Include both M=2.0 and M=3.0 as in reference case
            lines.append(f"MKAERO1 {aero.mach_number:<8.1f}{3.0:<8.1f}{'':48}+MK1     ")
            # Continuation card with validated reduced frequencies (MUST have leading zeros)
            lines.append("+MK1    0.001   0.1     0.2     0.4")
            lines.append("$")
        else:
            # MKAERO1 for doublet lattice (CAERO1)
            lines.append("$ Aerodynamic Matrices - Doublet Lattice (MKAERO1)")
            # Main card with Mach number only
            lines.append(f"MKAERO1 {aero.mach_number:<8.1f}{'':56}+MK1     ")
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

    # Extract material config (NASTRAN units: mm-kg-s-N)
    material = MaterialConfig(
        youngs_modulus=config.get('youngs_modulus', 71700.0),  # MPa (N/mm^2)
        poissons_ratio=config.get('poissons_ratio', 0.33),
        density=config.get('density', 2.81e-6)  # kg/mm^3
    )

    # Extract aero config
    aero = AeroConfig(
        mach_number=config.get('mach_number', 3.0),
        reference_velocity=config.get('velocity', 1.0e6),  # mm/s
        reference_chord=config.get('panel_length', 1000.0),  # mm
        reference_density=1.225e-9,  # kg/mm^3 (air at sea level)
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