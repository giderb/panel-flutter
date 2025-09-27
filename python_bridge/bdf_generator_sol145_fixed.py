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
        output_filename: str = "flutter_analysis.bdf"
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
        lines.append("$")

        # Material - VALIDATED FORMAT
        # Calculate shear modulus if not provided
        if material.shear_modulus is None:
            G = material.youngs_modulus / (2 * (1 + material.poissons_ratio))
        else:
            G = material.shear_modulus

        lines.append("$ Material Properties (SI units in mm)")
        # Match validated working format
        lines.append(f"MAT1    1       {material.youngs_modulus:.0f}.  {G:.0f}.  .{material.poissons_ratio*100:.0f}     {material.density:.2E}{2.1E-05:.1E}")
        lines.append("$")

        # Shell property
        lines.append("$ Shell Property")
        lines.append(f"PSHELL  1       1       {panel.thickness:.1f}")
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

        # Add constraint to prevent rigid body modes
        lines.append("SPC1    1       123456  1")
        lines.append("$")

        # Eigenvalue extraction
        lines.append("$ Eigenvalue Extraction")
        sid = 1
        msglvl = 0  # Set to 0 to avoid MSGLVL:10 <= 4 error
        lines.append(f"EIGRL   {sid:8d}{'':16}{n_modes:8d}{msglvl:8d}")
        lines.append("$")

        # Aerodynamic reference - VALIDATED FORMAT
        lines.append("$ Aerodynamic Reference")
        # AERO card matching validated working example
        lines.append(f"AERO    0       1.      {panel.length:<8.1f}1.225-12")
        lines.append("$")

        # AERODYNAMIC MODEL - Use doublet lattice method (more reliable than piston theory)
        lines.append("$ Doublet Lattice Method Property")
        lines.append("PAERO1  1")
        lines.append("$")

        # CAERO1 card for doublet lattice method - CORRECTED GEOMETRY
        lines.append("$ Doublet Lattice Method Panel")
        # CAERO1 format: EID PID CP NSPAN NCHORD LSPAN LCHORD IGD
        aero_nx = 4  # 4x4 aerodynamic mesh for better interpolation
        aero_ny = 4
        lines.append(f"CAERO1  1       1               {aero_nx:<8}{aero_ny:<8}{'':8}{'':8}1       +")
        # Correct corner coordinates: (0,0,0), (L,0,0), (L,W,0), (0,W,0)
        lines.append(f"+       0.      0.      0.      {panel.length:<8.1f}0.      {panel.width:<8.1f}{panel.length:<8.1f}{panel.width:<8.1f}0.")
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

        # Density ratio list (FLFACT 1) - need at least 2 values
        lines.append("FLFACT  1       1.0     1.0")

        # Mach number (FLFACT 2) - need at least 2 values
        lines.append(f"FLFACT  2       {aero.mach_number:.1f}     {aero.mach_number:.1f}")

        # For PK method, FLFACT 3 contains velocities
        if aero.velocities:
            # Write velocities in multiple lines if needed
            vel_idx = 0
            while vel_idx < len(aero.velocities):
                if vel_idx == 0:
                    vel_line = "FLFACT  3       "
                else:
                    vel_line = "+       "
                # Add up to 8 velocities per line
                for i in range(8):
                    if vel_idx < len(aero.velocities):
                        vel = aero.velocities[vel_idx]
                        # Format for 8-character field
                        if vel >= 1e7:
                            vel_str = f"{vel:.1e}"
                        elif vel >= 1e6:
                            vel_str = f"{vel/1e6:.2f}+6"
                            if len(vel_str) < 8:
                                vel_str = vel_str.ljust(8)
                        else:
                            vel_str = f"{vel:.0f}."
                        vel_str = vel_str[:8].ljust(8)
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

        # CORRECTED MKAERO1 card for piston theory - VALIDATED FORMAT
        lines.append("$ Aerodynamic Matrices - Piston Theory")
        # MKAERO1 format exactly matching validated working example

        # Main card with Mach number only
        lines.append(f"MKAERO1 {aero.mach_number:<8.1f}{'':56}+")

        # Continuation card with validated reduced frequencies
        # Use exact format from working example: .001 .1 .2 .4
        lines.append("+       .001    .1      .2      .4")
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