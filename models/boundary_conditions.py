"""
Boundary Condition Definitions for Panel Flutter Analysis
==========================================================
Comprehensive boundary condition types for rectangular panels.

Notation:
- S = Simply Supported (constrain w=0, allow rotation)
- C = Clamped (constrain w=0, θx=0, θy=0)
- F = Free (no constraints)

Edge order: Bottom-Right-Top-Left (clockwise from bottom)
Example: SSSS = Simply supported on all four edges
"""

from enum import Enum
from typing import List, Tuple
from dataclasses import dataclass

class BoundaryConditionType(Enum):
    """Enum for standard boundary condition types"""

    # All edges same
    SSSS = "SSSS"  # Simply supported on all 4 edges (most common)
    CCCC = "CCCC"  # Clamped on all 4 edges
    FFFF = "FFFF"  # Free on all 4 edges (space structures)

    # Cantilevered configurations
    CFFF = "CFFF"  # Cantilevered from left edge
    FCFF = "FCFF"  # Cantilevered from bottom edge
    FFCF = "FFCF"  # Cantilevered from right edge
    FFFC = "FFFC"  # Cantilevered from top edge

    # Two opposite edges constrained
    CFCF = "CFCF"  # Clamped at left and right, free at top and bottom
    FCFC = "FCFC"  # Free at left and right, clamped at top and bottom
    SFSF = "SFSF"  # Simply supported at left and right, free at top and bottom
    FSFS = "FSFS"  # Free at left and right, simply supported at top and bottom

    # Mixed boundary conditions
    SCSC = "SCSC"  # Simply supported-Clamped pattern
    CSCS = "CSCS"  # Clamped-Simply supported pattern

    # Three edges constrained, one free
    CCCF = "CCCF"  # Three edges clamped, top free
    CFCC = "CFCC"  # Bottom and sides clamped, right free (rotated CCCF)
    CCFC = "CCFC"  # Top and sides clamped, bottom free
    FCCC = "FCCC"  # Three edges clamped, left free

    SSSF = "SSSF"  # Three edges simply supported, top free
    SFSS = "SFSS"  # Simply supported except right edge free
    SSFS = "SSFS"  # Simply supported except bottom free
    FSSS = "FSSS"  # Simply supported except left edge free

    SCCS = "SCCS"  # Simply-Clamped-Clamped-Simply
    CSSC = "CSSC"  # Clamped-Simply-Simply-Clamped
    SCSS = "SCSS"  # Simply-Clamped-Simply-Simply

@dataclass
class EdgeConstraint:
    """Constraint definition for a panel edge"""
    edge_type: str  # 'S', 'C', or 'F'
    constrained_dofs: List[int]  # List of DOFs to constrain (1-6)
    description: str

class BoundaryConditionSpec:
    """Complete specification for boundary conditions"""

    # DOF definitions for NASTRAN
    DOF_TX = 1  # Translation X
    DOF_TY = 2  # Translation Y
    DOF_TZ = 3  # Translation Z (out-of-plane)
    DOF_RX = 4  # Rotation about X
    DOF_RY = 5  # Rotation about Y
    DOF_RZ = 6  # Rotation about Z (drilling)

    @staticmethod
    def get_edge_constraint(edge_type: str) -> EdgeConstraint:
        """Get constraint specification for an edge type"""
        if edge_type == 'S':
            # Simply Supported: constrain only out-of-plane displacement
            return EdgeConstraint(
                edge_type='S',
                constrained_dofs=[3],  # w = 0
                description="Simply Supported: w=0, rotations free"
            )
        elif edge_type == 'C':
            # Clamped: constrain all translations and rotations
            return EdgeConstraint(
                edge_type='C',
                constrained_dofs=[1, 2, 3, 4, 5, 6],  # All DOFs
                description="Clamped: All displacements and rotations = 0"
            )
        elif edge_type == 'F':
            # Free: no constraints
            return EdgeConstraint(
                edge_type='F',
                constrained_dofs=[],
                description="Free: No constraints"
            )
        else:
            raise ValueError(f"Unknown edge type: {edge_type}")

    @staticmethod
    def parse_bc_string(bc_string: str) -> Tuple[str, str, str, str]:
        """
        Parse boundary condition string into individual edges.

        Args:
            bc_string: 4-character string like "SSSS", "CFCF", etc.

        Returns:
            Tuple of (bottom, right, top, left) edge types
        """
        bc_string = bc_string.upper().strip()

        if len(bc_string) != 4:
            raise ValueError(f"Boundary condition string must be 4 characters, got: {bc_string}")

        for char in bc_string:
            if char not in ['S', 'C', 'F']:
                raise ValueError(f"Invalid character '{char}' in boundary condition. Use S, C, or F only.")

        # Edge order: Bottom-Right-Top-Left (clockwise from bottom)
        return (bc_string[0], bc_string[1], bc_string[2], bc_string[3])

    @staticmethod
    def get_description(bc_type: BoundaryConditionType) -> str:
        """Get detailed description of a boundary condition type"""
        descriptions = {
            BoundaryConditionType.SSSS: "Simply supported on all four edges - typical aircraft panel",
            BoundaryConditionType.CCCC: "Clamped on all four edges - rigid attachment",
            BoundaryConditionType.FFFF: "Free on all four edges - space structure, no attachment",
            BoundaryConditionType.CFFF: "Cantilever: clamped at left edge, free elsewhere",
            BoundaryConditionType.CFCF: "Clamped at left/right edges, free at top/bottom - typical for stiffened panels",
            BoundaryConditionType.FCFC: "Free at left/right edges, clamped at top/bottom",
            BoundaryConditionType.SFSF: "Simply supported at left/right edges, free at top/bottom",
            BoundaryConditionType.FSFS: "Free at left/right edges, simply supported at top/bottom",
            BoundaryConditionType.SCSC: "Simply-Clamped-Simply-Clamped pattern",
            BoundaryConditionType.CSCS: "Clamped-Simply-Clamped-Simply pattern",
            BoundaryConditionType.CCCF: "Three edges clamped, top edge free",
            BoundaryConditionType.SSSF: "Three edges simply supported, top edge free",
            BoundaryConditionType.SCCS: "Simply-Clamped-Clamped-Simply",
        }
        return descriptions.get(bc_type, f"Boundary condition: {bc_type.value}")

    @staticmethod
    def requires_rigid_body_constraints(bc_string: str) -> bool:
        """
        Determine if additional rigid body mode constraints are needed.

        Free-free panels need special handling to prevent rigid body modes.
        """
        bc_upper = bc_string.upper()

        # If all edges are free, need rigid body constraints
        if bc_upper == "FFFF":
            return True

        # Count constrained edges
        constrained_count = sum(1 for char in bc_upper if char in ['S', 'C'])

        # If less than 2 edges constrained, may need additional constraints
        return constrained_count < 2

    @staticmethod
    def validate_bc_string(bc_string: str) -> Tuple[bool, str]:
        """
        Validate a boundary condition string.

        Returns:
            (is_valid, error_message)
        """
        try:
            bottom, right, top, left = BoundaryConditionSpec.parse_bc_string(bc_string)

            # All valid configurations
            valid_configs = [bc.value for bc in BoundaryConditionType]

            if bc_string.upper() in valid_configs:
                return (True, "")
            else:
                return (True, f"Warning: Uncommon boundary condition '{bc_string}' - ensure it's correct")

        except ValueError as e:
            return (False, str(e))

def get_all_boundary_conditions() -> List[BoundaryConditionType]:
    """Get list of all supported boundary conditions"""
    return list(BoundaryConditionType)

def get_common_boundary_conditions() -> List[BoundaryConditionType]:
    """Get list of most commonly used boundary conditions"""
    return [
        BoundaryConditionType.SSSS,
        BoundaryConditionType.CCCC,
        BoundaryConditionType.CFFF,
        BoundaryConditionType.CFCF,
        BoundaryConditionType.SFSF,
        BoundaryConditionType.SCSC,
    ]
