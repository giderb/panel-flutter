"""
Template-Based BDF Generator for CAERO5 Piston Theory
======================================================
Uses validated template to bypass pyNastran CAERO5 API bugs
"""

from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class TemplateBDFGenerator:
    """
    Generates NASTRAN BDF files using validated CAERO5 template.
    Bypasses pyNastran API issues with CAERO5/PAERO5 cards.
    """

    def __init__(self):
        self.template_path = Path(__file__).parent.parent / 'templates' / 'sol145_caero5_template.bdf'
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")

    def generate_caero5_flutter_bdf(
        self,
        length: float,
        width: float,
        thickness: float,
        nx: int,
        ny: int,
        youngs_modulus: float,
        poissons_ratio: float,
        density: float,
        mach_number: float,
        velocities: List[float],
        boundary_conditions: str = "SSSS",
        output_file: str = "flutter_analysis.bdf"
    ) -> str:
        """
        Generate BDF file from template with CAERO5 for panel flutter.

        All units in SI (m, kg, Pa, m/s)
        """

        logger.info(f"Generating CAERO5 BDF from template for M={mach_number:.2f}")

        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()

        # Generate GRID cards
        grid_cards = self._generate_grid_cards(nx, ny, length, width)

        # Generate ELEMENT cards (CQUAD4)
        element_cards = self._generate_element_cards(nx, ny)

        # Generate SPC cards with rotational constraints (FIXED grid point singularity)
        spc_cards = self._generate_spc_cards(nx, ny, boundary_conditions)

        # Generate CAERO5 geometry line - CRITICAL: Fixed field format, 8-char fields
        # Format: X1(8) Y1(8) Z1(8) X12(8) X4(8) Y4(8) Z4(8) X43(8)
        # CAERO5 child line must start with 8 spaces for implicit continuation
        caero_child = f"{0.0:8.4f}{0.0:8.4f}{0.0:8.4f}{length:8.4f}{0.0:8.4f}{width:8.4f}{0.0:8.4f}{length:8.4f}"

        # Generate AEFACT 3001 (spanwise distribution)
        span_positions = [i / ny for i in range(ny + 1)]
        aefact_3001 = self._format_aefact(3001, span_positions)

        # Generate CAOCI cards (not used for simple panels)
        caoci_cards = "$CAOCI cards not required for simple rectangular panel"

        # Generate velocity FLFACT card
        velocity_flfact = self._generate_velocity_flfact(velocities)

        # Generate Mach card for MKAERO2
        mach_card = f"{mach_number:8.3f}"

        # Calculate BOX2 for SPLINE1 (last aerodynamic box)
        box2 = 1001 + ny - 1
        box2_str = f"{box2:8d}"  # Format as 8-char integer field

        # Calculate SET cards (aerodynamic boxes)
        set_cards = self._generate_set_cards(ny)

        # Format numerical values
        thickness_str = f"{thickness:8.6f}"
        youngs_mod_str = f"{youngs_modulus:.3E}".replace('E+', '+').replace('E-', '-')
        poisson_str = f"{poissons_ratio:8.4f}"
        density_str = f"{density:.3E}".replace('E+', '+').replace('E-', '-')
        ref_vel_str = f"{velocities[len(velocities)//2]:8.1f}"  # Middle velocity as reference
        length_str = f"{length:8.3f}"

        # Replace placeholders
        bdf_content = template.format(
            MACH=mach_number,
            NX=nx,
            NY=ny,
            GRID_CARDS=grid_cards,
            ELEMENT_CARDS=element_cards,
            THICKNESS=thickness_str,
            YOUNGS_MOD=youngs_mod_str,
            POISSON=poisson_str,
            DENSITY=density_str,
            CAERO_CHILD_LINE=caero_child,
            CAOCI_CARDS=caoci_cards,
            BOX2=box2_str,
            AEFACT_3001=aefact_3001,
            REF_VEL=ref_vel_str,
            L=length_str,
            MACH_CARD=mach_card,
            VELOCITY_FLFACT=velocity_flfact,
            SPC_CARDS=spc_cards,
            SET_CARDS=set_cards
        )

        # Write BDF file
        with open(output_file, 'w') as f:
            f.write(bdf_content)

        logger.info(f"CAERO5 BDF generated successfully: {output_file}")
        return output_file

    def _generate_grid_cards(self, nx: int, ny: int, length: float, width: float) -> str:
        """Generate GRID cards"""
        cards = []
        grid_id = 1
        dx = length / nx
        dy = width / ny

        for j in range(ny + 1):
            for i in range(nx + 1):
                x = i * dx
                y = j * dy
                z = 0.0
                cards.append(f"GRID    {grid_id:8d}        {x:8.4f}{y:8.4f}{z:8.4f}")
                grid_id += 1

        return '\n'.join(cards)

    def _generate_element_cards(self, nx: int, ny: int) -> str:
        """Generate CQUAD4 element cards"""
        cards = []
        elem_id = 1

        for j in range(ny):
            for i in range(nx):
                n1 = j * (nx + 1) + i + 1
                n2 = n1 + 1
                n3 = n1 + nx + 2
                n4 = n1 + nx + 1
                cards.append(f"CQUAD4  {elem_id:8d}       1{n1:8d}{n2:8d}{n3:8d}{n4:8d}")
                elem_id += 1

        return '\n'.join(cards)

    def _generate_spc_cards(self, nx: int, ny: int, boundary_conditions: str) -> str:
        """
        Generate SPC cards with rotational constraints.
        CRITICAL FIX: Includes rotational DOFs to eliminate grid point singularities.
        """
        cards = []

        if boundary_conditions.upper() == "SSSS":
            # Simply supported: W=0 and normal rotation=0 on edges
            # Plus in-plane constraints at corners for rigid body prevention

            # Collect edge nodes by edge
            bottom_edge = [i + 1 for i in range(nx + 1)]  # j=0
            top_edge = [ny * (nx + 1) + i + 1 for i in range(nx + 1)]  # j=ny
            left_edge = [j * (nx + 1) + 1 for j in range(ny + 1)]  # i=0
            right_edge = [j * (nx + 1) + nx + 1 for j in range(ny + 1)]  # i=nx

            # Bottom/Top edges: W (3) + θy (5) - rotation about Y, normal to X-edge
            for nodes in [bottom_edge, top_edge]:
                cards.append(self._format_spc1(1, '35', nodes))

            # Left/Right edges: W (3) + θx (4) - rotation about X, normal to Y-edge
            for nodes in [left_edge, right_edge]:
                cards.append(self._format_spc1(1, '34', nodes))

            # Corner constraints for rigid body prevention
            # Bottom-left: U, V (in-plane)
            cards.append(f"SPC1           1      12       1")

            # Bottom-right: V only
            cards.append(f"SPC1           1       2{nx + 1:8d}")

        return '\n'.join(cards)

    def _format_spc1(self, conid: int, components: str, nodes: List[int]) -> str:
        """Format SPC1 card with continuation if needed"""
        # NASTRAN SPC1 format: up to 6 nodes per line, continue if more
        lines = []
        for i in range(0, len(nodes), 6):
            chunk = nodes[i:i+6]
            if i == 0:
                # First line
                node_str = ''.join(f"{n:8d}" for n in chunk)
                lines.append(f"SPC1    {conid:8d}{components:>8s}{node_str}")
            else:
                # Continuation
                node_str = ''.join(f"{n:8d}" for n in chunk)
                lines.append(f"+       {node_str}")

        return '\n'.join(lines)

    def _format_aefact(self, sid: int, values: List[float]) -> str:
        """Format AEFACT card"""
        val_str = ''.join(f"{v:8.4f}" for v in values)
        return f"AEFACT  {sid:8d}{val_str}"

    def _generate_velocity_flfact(self, velocities: List[float]) -> str:
        """Generate FLFACT 13 card for velocities"""
        # FLFACT format: up to 8 values per line
        lines = []
        for i in range(0, len(velocities), 8):
            chunk = velocities[i:i+8]
            vel_str = ''.join(f"{v:8.1f}" for v in chunk)
            if i == 0:
                lines.append(f"FLFACT        13{vel_str}")
            else:
                lines.append(f"+               {vel_str}")

        return '\n'.join(lines)

    def _generate_set_cards(self, ny: int) -> str:
        """Generate SET cards for aerodynamic boxes"""
        # Each strip is one aerodynamic box
        boxes = [1001 + i for i in range(ny)]
        box_str = ''.join(f"{b:8d}" for b in boxes)
        return f"SET1           1{box_str}"
