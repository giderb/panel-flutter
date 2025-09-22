"""
WORKING NASTRAN BDF File Generator for Flutter Analysis
========================================================

Generates proper NASTRAN Bulk Data Files for panel flutter analysis
with correct 8-character fixed field formatting.
"""

import numpy as np
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


class WorkingBDFGenerator:
    """Working NASTRAN BDF file generator for flutter analysis"""

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
        """Generate a working NASTRAN BDF file for flutter analysis"""

        filepath = self.output_dir / output_filename
        lines = []

        # Header comments
        lines.append("$ WORKING NASTRAN FLUTTER ANALYSIS")
        lines.append(f"$ Generated: {datetime.datetime.now()}")
        lines.append(f"$ Panel: {panel.length}mm x {panel.width}mm")
        lines.append("$")

        # Executive control
        lines.append("SOL 145")
        lines.append("CEND")

        # Case control
        lines.append("TITLE = Panel Flutter Analysis")
        lines.append("ECHO = NONE")
        lines.append("SPC = 1")
        lines.append("METHOD = 1")
        lines.append("FMETHOD = 1")
        lines.append("BEGIN BULK")
        lines.append("$")

        # Parameters
        lines.append("PARAM   COUPMASS1")
        lines.append("PARAM   GRDPNT  0")
        # WTMASS not needed when density is specified directly in MAT1
        # For SI units in mm, if needed: WTMASS = 1/g = 1/9810 = 1.019e-4
        lines.append("$")

        # Material (convert to NASTRAN units)
        # Calculate shear modulus if not provided
        if material.shear_modulus is None:
            G = material.youngs_modulus / (2 * (1 + material.poissons_ratio))
        else:
            G = material.shear_modulus

        lines.append("$ Material Properties (SI units in mm)")
        # Format: MAT1 MID E G NU RHO
        # Note: E and G should be in MPa (N/mm^2), density in ton/mm^3
        # Use scientific notation for large values to fit in 8 characters
        mat1_line = "MAT1    "
        mat1_line += f"{1:8d}"  # MID (field 2)
        # Use scientific notation for E and G to fit in 8 characters
        mat1_line += f"{material.youngs_modulus:8.2e}"  # E (field 3)
        mat1_line += f"{G:8.2e}"  # G (field 4)
        mat1_line += f"{material.poissons_ratio:8.3f}"  # NU (field 5)
        mat1_line += f"{material.density:8.2e}"  # RHO (field 6)
        lines.append(mat1_line)
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
                    spc_line = "+       "  # Use + marker for continuation
                spc_line += f"{node:<8}"
            if spc_line.strip():
                lines.append(spc_line)
        lines.append("$")

        # Eigenvalue extraction
        lines.append("$ Eigenvalue Extraction")
        # EIGRL with MSGLVL field to avoid fatal error
        sid = 1
        msglvl = 0  # Set to 0 to avoid MSGLVL:10 <= 4 error
        # Format: field 1=EIGRL, field 2=SID, fields 3-4 blank, field 5=ND, field 6=MSGLVL
        lines.append(f"EIGRL   {sid:8d}{'':16}{n_modes:8d}{msglvl:8d}")
        lines.append("$")

        # Aerodynamic reference
        lines.append("$ Aerodynamic Reference")
        # AERO card: Field 3=velocity scale, Field 4=chord, Field 5=density, Fields 6-7=symmetry
        # Use actual reference values from aero config
        # Format density in scientific notation for NASTRAN
        rho_ref = aero.reference_density if aero.reference_density else 1.225e-9  # kg/mm³
        chord_ref = aero.reference_chord if aero.reference_chord else panel.length  # mm
        # Ensure proper formatting for small numbers
        rho_str = f"{rho_ref:.3e}".replace('e-0', 'e-').replace('e+0', 'e+')
        lines.append(f"AERO    0       1.0e6   {chord_ref:<8.1f}{rho_str:<8}1       0")
        lines.append("$")

        # Aerodynamic panel property
        lines.append("PAERO1  1")
        lines.append("$")

        # CAERO1 panel - needs proper continuation format
        lines.append("$ Aerodynamic Panel")
        # CAERO1 with blank CP field (not 0)
        lines.append(f"CAERO1  1001    1               {panel.ny:<8}{panel.nx:<8}        0       1")
        # Single continuation line with proper field widths (8 chars each)
        x1, y1, z1 = 0.0, 0.0, 0.0
        x12 = panel.length
        x4, y4, z4 = 0.0, panel.width, 0.0
        x43 = panel.length
        # Format with exactly 8 characters per field
        cont_line = "+       "
        cont_line += f"{x1:8.1f}{y1:8.1f}{z1:8.1f}{x12:8.1f}"
        cont_line += f"{x4:8.1f}{y4:8.1f}{z4:8.1f}{x43:8.1f}"
        lines.append(cont_line)
        lines.append("$")

        # Spline - use SPLINE1 to avoid singular matrix error
        lines.append("$ Spline")
        n_aero_boxes = panel.nx * panel.ny
        lines.append(f"SPLINE1 1       1001    1001    {1001 + n_aero_boxes - 1:<8}1")
        lines.append(f"SET1    1       1       THRU    {(panel.nx + 1) * (panel.ny + 1)}")
        lines.append("$")

        # Flutter cards
        lines.append("$ Flutter Analysis")
        # FLUTTER card: PK method with density (1), Mach (2), reduced freq/velocity (3)
        # The last field should be interpolation method (L, S, or TCUB), not a FLFACT ID
        lines.append("FLUTTER 1       PK      1       2       3       L")

        # Density ratio list (FLFACT 1)
        lines.append("FLFACT  1       1.0")

        # Mach number (FLFACT 2)
        lines.append(f"FLFACT  2       {aero.mach_number:.1f}")

        # For V-g/PK method, FLFACT 3 contains velocities (not reduced frequencies)
        # Velocities are the key for flutter speed detection
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
                        # Format for 8-character field - use simple notation
                        if vel >= 1e7:
                            vel_str = f"{vel:.1e}"
                        elif vel >= 1e6:
                            # Format with +6 notation, ensuring 8 characters
                            vel_str = f"{vel/1e6:.2f}+6"
                            if len(vel_str) < 8:
                                vel_str = vel_str.ljust(8)
                        else:
                            vel_str = f"{vel:.0f}."
                        # Make sure it's exactly 8 characters
                        vel_str = vel_str[:8].ljust(8)
                        vel_line += vel_str
                        vel_idx += 1
                    else:
                        break
                # Don't strip trailing spaces - NASTRAN needs fixed 8-char fields
                lines.append(vel_line)
        else:
            # Default velocity range in mm/s (500-1500 m/s)
            lines.append("FLFACT  3       5.0E+05 6.0E+05 7.0E+05 8.0E+05 9.0E+05 1.0E+06 1.1E+06 1.2E+06")
            lines.append("+       1.3E+06 1.4E+06 1.5E+06")
        lines.append("$")

        # MKAERO1
        lines.append("$ Aerodynamic Matrices")
        # Always use the actual Mach number from aero config
        mkaero_line = "MKAERO1 "
        mkaero_line += f"{aero.mach_number:8.1f}"
        lines.append(mkaero_line)

        # Continuation line with reduced frequencies
        cont_line = "+       "
        if aero.reduced_frequencies:
            for k in aero.reduced_frequencies[:8]:
                cont_line += f"{k:8.3f}"
        else:
            # Default reduced frequencies if not provided
            for k in [0.001, 0.010, 0.100, 0.200]:
                cont_line += f"{k:8.3f}"
        lines.append(cont_line)
        lines.append("$")

        # End of data
        lines.append("ENDDATA")

        # Write file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

        logger.info(f"Generated BDF file: {filepath}")
        return str(filepath)


def create_flutter_bdf(config: Dict[str, Any], output_dir: str = ".") -> str:
    """Create a flutter analysis BDF file from configuration"""

    generator = WorkingBDFGenerator(output_dir)

    # Extract panel config
    panel = PanelConfig(
        length=config.get('panel_length', 1000.0),  # mm
        width=config.get('panel_width', 800.0),      # mm
        thickness=config.get('thickness', 2.0),       # mm
        nx=config.get('nx', 2),
        ny=config.get('ny', 2)
    )

    # Extract material config (NASTRAN units: mm-kg-s-N)
    material = MaterialConfig(
        youngs_modulus=config.get('youngs_modulus', 71700.0),  # MPa (N/mm^2)
        poissons_ratio=config.get('poissons_ratio', 0.33),
        density=config.get('density', 2.81e-6)  # kg/mm^3 (aluminum: 2810 kg/m^3 = 2.81e-6 kg/mm^3)
    )

    # Extract aero config
    aero = AeroConfig(
        mach_number=config.get('mach_number', 0.8),
        reference_velocity=config.get('velocity', 1.0e6),  # mm/s
        reference_chord=config.get('panel_length', 1000.0),  # mm
        reference_density=1.225e-9,  # kg/mm^3 (air at sea level: 1.225 kg/m^3 = 1.225e-9 kg/mm^3)
        reduced_frequencies=config.get('reduced_frequencies', [0.001, 0.1, 0.2, 0.4])
    )

    # Generate BDF
    return generator.generate_bdf(
        panel=panel,
        material=material,
        aero=aero,
        boundary_conditions=config.get('boundary_conditions', 'SSSS'),
        n_modes=config.get('n_modes', 10),
        output_filename=config.get('output_filename', 'flutter_analysis.bdf')
    )