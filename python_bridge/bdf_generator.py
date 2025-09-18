"""
NASTRAN BDF File Generator for Flutter Analysis
================================================

Generates proper NASTRAN Bulk Data Files for panel flutter analysis
matching the format used in Metallic.ipynb notebook.
"""

import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import datetime


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
    """Material properties for BDF"""
    youngs_modulus: float  # Pa
    poissons_ratio: float
    density: float  # kg/m³
    shear_modulus: Optional[float] = None
    thermal_expansion: Optional[float] = None
    material_id: int = 1


@dataclass
class AeroConfig:
    """Aerodynamic configuration for BDF"""
    mach_number: float
    reference_velocity: float  # m/s
    reference_chord: float  # m
    reference_density: float  # kg/m³
    reduced_frequencies: List[float] = None
    velocities: List[float] = None


class NastranBDFGenerator:
    """Generate NASTRAN BDF files for flutter analysis"""

    def __init__(self):
        self.card_count = 0

    def generate_flutter_bdf(self, panel: PanelConfig, material: MaterialConfig,
                           aero: AeroConfig, boundary_conditions: str = "SSSS",
                           output_path: Optional[Path] = None) -> str:
        """
        Generate complete BDF file for flutter analysis.

        This matches the format from the Metallic.ipynb notebook.
        """
        lines = []

        # Header
        lines.append("$ NASTRAN Panel Flutter Analysis")
        lines.append(f"$ Generated: {datetime.datetime.now()}")
        lines.append("$ Based on Metallic Panel Example")
        lines.append("$")

        # Executive Control
        lines.append("SOL 145")  # Flutter analysis
        lines.append("CEND")
        lines.append("")

        # Case Control
        lines.append("TITLE = Panel Flutter Analysis")
        lines.append("ECHO = NONE")
        lines.append("SPC = 1")
        lines.append("METHOD = 1")
        lines.append("FMETHOD = 1")
        lines.append("SET 1 = 1 THRU 999999")
        lines.append("DISPLACEMENT(PRINT,PUNCH) = 1")
        lines.append("SPCFORCES(PRINT,PUNCH) = 1")
        lines.append("STRESS(PRINT,PUNCH) = 1")
        lines.append("FORCE(PRINT,PUNCH) = 1")
        lines.append("BEGIN BULK")
        lines.append("")

        # PARAM cards
        lines.append("PARAM   COUPMASS1")
        lines.append("PARAM   GRDPNT  0")
        lines.append("PARAM   OPPHIPA 1")
        lines.append("PARAM   LMODES  15")
        lines.append("PARAM   VREF    1000.0")
        lines.append("")

        # Material card (MAT1)
        # Convert units: Pa to Pa for consistency
        lines.append(self._format_mat1(material))
        lines.append("")

        # Property card (PSHELL)
        lines.append(self._format_pshell(panel.property_id, material.material_id, panel.thickness))
        lines.append("")

        # Grid points (nodes)
        lines.extend(self._generate_grid_points(panel))
        lines.append("")

        # Elements (CQUAD4)
        lines.extend(self._generate_elements(panel))
        lines.append("")

        # Boundary conditions (SPC1)
        lines.extend(self._generate_boundary_conditions(panel, boundary_conditions))
        lines.append("")

        # Eigenvalue extraction (EIGRL)
        lines.append(self._format_eigrl())
        lines.append("")

        # Aerodynamic cards
        lines.append("$ Aerodynamic Configuration")
        lines.append(self._format_aero(aero))
        lines.append("")

        # CAERO panel
        lines.extend(self._generate_caero_panel(panel, aero))
        lines.append("")

        # PAERO cards
        lines.append("PAERO1  1001")
        lines.append("")

        # Spline cards
        lines.extend(self._generate_splines(panel))
        lines.append("")

        # FLUTTER card
        lines.append(self._format_flutter(aero))
        lines.append("")

        # FLFACT cards for flutter analysis
        lines.extend(self._generate_flfact_cards(aero))
        lines.append("")

        # MKAERO cards
        lines.extend(self._generate_mkaero_cards(aero))
        lines.append("")

        # End of file
        lines.append("ENDDATA")

        bdf_content = "\n".join(lines)

        # Save to file if path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(bdf_content)

        return bdf_content

    def _format_mat1(self, material: MaterialConfig) -> str:
        """Format MAT1 card for isotropic material"""
        # MAT1    MID     E       G       NU      RHO     A       TREF
        mid = material.material_id
        E = material.youngs_modulus
        G = material.shear_modulus or (E / (2 * (1 + material.poissons_ratio)))
        nu = material.poissons_ratio
        rho = material.density

        return f"MAT1    {mid:<8d}{E:<8.2E}{G:<8.2E}{nu:<8.3f}{rho:<8.2E}"

    def _format_pshell(self, pid: int, mid: int, thickness: float) -> str:
        """Format PSHELL card"""
        # PSHELL  PID     MID     T
        t = thickness
        return f"PSHELL  {pid:<8d}{mid:<8d}{t:<8.4f}"

    def _format_eigrl(self) -> str:
        """Format EIGRL card for eigenvalue extraction"""
        # EIGRL   SID     V1      V2      ND
        return "EIGRL   1               1000.0  15"

    def _format_aero(self, aero: AeroConfig) -> str:
        """Format AERO card"""
        # AERO    ACSID   VELOCITY REFC    RHOREF  SYMXZ   SYMXY
        refc = aero.reference_chord
        rhoref = aero.reference_density
        return f"AERO    0       {aero.reference_velocity:<8.1f}{refc:<8.3f}{rhoref:<8.2E}1       0"

    def _format_flutter(self, aero: AeroConfig) -> str:
        """Format FLUTTER card"""
        # FLUTTER ID      METHOD  DENS    MACH    RFREQ   IMETH
        return "FLUTTER 1       PK      11      12      13      L"

    def _generate_grid_points(self, panel: PanelConfig) -> List[str]:
        """Generate GRID cards for nodes"""
        lines = []
        lines.append("$ Grid Points")

        dx = panel.length / panel.nx
        dy = panel.width / panel.ny

        node_id = 1
        for j in range(panel.ny + 1):
            for i in range(panel.nx + 1):
                x = i * dx * 1000  # Convert to mm
                y = j * dy * 1000  # Convert to mm
                z = 0.0

                # GRID    ID      CP      X       Y       Z
                line = f"GRID    {node_id:<8d}0       {x:<8.3f}{y:<8.3f}{z:<8.3f}"
                lines.append(line)
                node_id += 1

        return lines

    def _generate_elements(self, panel: PanelConfig) -> List[str]:
        """Generate CQUAD4 elements"""
        lines = []
        lines.append("$ Elements")

        elem_id = 1
        for j in range(panel.ny):
            for i in range(panel.nx):
                # Node IDs for this element
                n1 = j * (panel.nx + 1) + i + 1
                n2 = n1 + 1
                n3 = n2 + panel.nx + 1
                n4 = n1 + panel.nx + 1

                # CQUAD4  EID     PID     N1      N2      N3      N4
                line = f"CQUAD4  {elem_id:<8d}{panel.property_id:<8d}{n1:<8d}{n2:<8d}{n3:<8d}{n4:<8d}"
                lines.append(line)
                elem_id += 1

        return lines

    def _generate_boundary_conditions(self, panel: PanelConfig, bc_type: str) -> List[str]:
        """Generate SPC1 cards for boundary conditions"""
        lines = []
        lines.append("$ Boundary Conditions")

        total_nodes = (panel.nx + 1) * (panel.ny + 1)

        if bc_type == "SSSS":
            # Simply supported on all edges
            # Constrain Z displacement and rotations on edges
            edge_nodes = []

            # Bottom edge
            edge_nodes.extend(range(1, panel.nx + 2))
            # Top edge
            edge_nodes.extend(range(total_nodes - panel.nx, total_nodes + 1))
            # Left edge
            for j in range(panel.ny + 1):
                edge_nodes.append(j * (panel.nx + 1) + 1)
            # Right edge
            for j in range(panel.ny + 1):
                edge_nodes.append((j + 1) * (panel.nx + 1))

            # Remove duplicates
            edge_nodes = list(set(edge_nodes))

            # SPC1 for Z displacement
            for node in edge_nodes:
                lines.append(f"SPC1    1       3       {node}")

        elif bc_type == "CCCC":
            # Clamped on all edges
            # Constrain all DOFs on edges
            edge_nodes = []

            # Similar to SSSS but constrain all 6 DOFs
            # Implementation would be similar...
            pass

        return lines

    def _generate_caero_panel(self, panel: PanelConfig, aero: AeroConfig) -> List[str]:
        """Generate CAERO1 cards for aerodynamic panels"""
        lines = []
        lines.append("$ Aerodynamic Panels")

        # Convert to mm for NASTRAN
        x1 = 0.0
        y1 = 0.0
        x2 = panel.length * 1000
        y2 = panel.width * 1000

        # CAERO1  EID     PID     CP      NSPAN   NCHORD  LSPAN   LCHORD  IGD
        lines.append(f"CAERO1  1001    1001    0       {panel.ny:<8d}{panel.nx:<8d}        1       1")
        # Continuation card with corner coordinates (x1,y1,z1,x12)
        lines.append(f"        {x1:<8.1f}{y1:<8.1f}0.0     {x2-x1:<8.1f}")
        # Second continuation (x4,y4,z4,x43)
        lines.append(f"        {x1:<8.1f}{y2:<8.1f}0.0     {x2-x1:<8.1f}")

        return lines

    def _generate_splines(self, panel: PanelConfig) -> List[str]:
        """Generate SPLINE cards to connect structure to aerodynamics"""
        lines = []
        lines.append("$ Splines")

        # SPLINE2 connects aerodynamic panels to structural nodes
        # SPLINE2 EID     CAERO   BOX1    BOX2    SETG    DZ      DTOR    CID
        lines.append("SPLINE2 1       1001    1001    1400    1       0.0     1.0     0")

        # SET1 for all structural nodes
        total_nodes = (panel.nx + 1) * (panel.ny + 1)
        lines.append(f"SET1    1       1       THRU    {total_nodes}")

        return lines

    def _generate_flfact_cards(self, aero: AeroConfig) -> List[str]:
        """Generate FLFACT cards for flutter parameters"""
        lines = []

        # Density ratios
        lines.append("$ Density Ratios")
        lines.append("FLFACT  11      0.5     1.0     1.5")

        # Mach numbers
        lines.append("$ Mach Numbers")
        lines.append(f"FLFACT  12      {aero.mach_number:.1f}")

        # Reduced frequencies
        lines.append("$ Reduced Frequencies")
        if aero.reduced_frequencies:
            rfreqs = " ".join([f"{k:.3f}" for k in aero.reduced_frequencies[:8]])
            lines.append(f"FLFACT  13      {rfreqs}")
        else:
            lines.append("FLFACT  13      0.001   0.1     0.2     0.4     0.6     0.8     1.0")

        # Velocities
        lines.append("$ Velocities")
        if aero.velocities:
            # Take subset of velocities for BDF (max 8 per card)
            vels = aero.velocities[::5][:8]  # Every 5th velocity, max 8
            # Format each velocity in fixed 8-character fields
            vel_fields = []
            for v in vels:
                vel_fields.append(f"{v:<8.1f}")
            # Join first few fields for the main card
            main_fields = vel_fields[:7] if len(vel_fields) > 7 else vel_fields
            lines.append(f"FLFACT  14      {''.join(main_fields)}")
            # Add continuation if needed
            if len(vel_fields) > 7:
                lines.append(f"        {vel_fields[7]}")
        else:
            lines.append("FLFACT  14      800.0   900.0   1000.0  1100.0  1200.0")

        return lines

    def _generate_mkaero_cards(self, aero: AeroConfig) -> List[str]:
        """Generate MKAERO cards for aerodynamic matrix generation"""
        lines = []
        lines.append("$ MKAERO Cards")

        # Generate for a few Mach numbers and reduced frequencies
        machs = [aero.mach_number]
        if aero.reduced_frequencies:
            ks = aero.reduced_frequencies[:4]
        else:
            ks = [0.001, 0.1, 0.2, 0.4]

        # MKAERO1 cards - all Mach/k pairs on one card with proper continuation
        # First card with MKAERO1 keyword
        lines.append(f"MKAERO1 {machs[0]:<8.2f}{ks[0]:<8.3f}{machs[0]:<8.2f}{ks[1]:<8.3f}" if len(ks) > 1 else f"MKAERO1 {machs[0]:<8.2f}{ks[0]:<8.3f}")

        # Add continuation lines if more k values
        if len(ks) > 2:
            lines.append(f"        {machs[0]:<8.2f}{ks[2]:<8.3f}" + (f"{machs[0]:<8.2f}{ks[3]:<8.3f}" if len(ks) > 3 else ""))

        return lines


def generate_metallic_panel_bdf():
    """Generate BDF file for the metallic panel example"""

    # Panel configuration (300mm x 300mm x 1.5mm)
    panel = PanelConfig(
        length=0.3,  # m
        width=0.3,   # m
        thickness=0.0015,  # m
        nx=20,
        ny=20
    )

    # Material (Aluminum 6061-T6)
    material = MaterialConfig(
        youngs_modulus=71.7e9,  # Pa
        poissons_ratio=0.33,
        density=2810,  # kg/m³
    )

    # Aerodynamic configuration
    aero = AeroConfig(
        mach_number=3.0,
        reference_velocity=1000.0,
        reference_chord=0.3,
        reference_density=1.225e-12,
        reduced_frequencies=[0.001, 0.1, 0.2, 0.4],
        velocities=list(range(822, 1063, 5))  # 822-1062 m/s in steps of 5
    )

    generator = NastranBDFGenerator()
    bdf_content = generator.generate_flutter_bdf(
        panel, material, aero,
        boundary_conditions="SSSS"
    )

    return bdf_content


if __name__ == "__main__":
    # Generate and print sample BDF
    bdf = generate_metallic_panel_bdf()
    print(bdf[:2000])  # Print first 2000 characters
    print("\n... (truncated) ...")
    print(f"\nTotal lines: {len(bdf.splitlines())}")

    # Save to file
    with open("metallic_panel_flutter.bdf", "w") as f:
        f.write(bdf)
    print("\nBDF saved to: metallic_panel_flutter.bdf")