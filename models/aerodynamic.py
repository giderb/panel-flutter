"""Aerodynamic model definitions for NASTRAN panel flutter analysis."""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np


class AerodynamicTheory(Enum):
    """Aerodynamic theory types."""
    PISTON_THEORY = "PISTON_THEORY"  # CAERO5 - High supersonic flows
    DOUBLET_LATTICE = "DOUBLET_LATTICE"  # CAERO1 - Subsonic flows
    ZAERO = "ZAERO"  # ZAERO - Advanced aerodynamics


class FlowType(Enum):
    """Flow type definitions."""
    SUBSONIC = "SUBSONIC"
    TRANSONIC = "TRANSONIC"
    SUPERSONIC = "SUPERSONIC"
    HYPERSONIC = "HYPERSONIC"


@dataclass
class FlowConditions:
    """Flow condition parameters."""
    mach_number: float
    dynamic_pressure: float  # Pa
    altitude: float = 0.0  # m
    temperature: float = 288.15  # K (ISA standard)
    pressure: float = 101325.0  # Pa (ISA standard)
    density: float = 1.225  # kg/m³ (ISA standard)

    def __post_init__(self):
        if self.mach_number <= 0:
            raise ValueError("Mach number must be positive")
        if self.dynamic_pressure <= 0:
            raise ValueError("Dynamic pressure must be positive")

    @property
    def flow_type(self) -> FlowType:
        """Determine flow type based on Mach number."""
        if self.mach_number < 0.8:
            return FlowType.SUBSONIC
        elif self.mach_number < 1.2:
            return FlowType.TRANSONIC
        elif self.mach_number < 5.0:
            return FlowType.SUPERSONIC
        else:
            return FlowType.HYPERSONIC

    @property
    def speed_of_sound(self) -> float:
        """Calculate speed of sound."""
        gamma = 1.4  # Specific heat ratio for air
        R = 287.0  # Gas constant for air (J/kg·K)
        return np.sqrt(gamma * R * self.temperature)

    @property
    def flow_velocity(self) -> float:
        """Calculate flow velocity."""
        return self.mach_number * self.speed_of_sound


@dataclass
class PistonTheoryParameters:
    """Piston theory aerodynamic parameters."""
    gamma: float = 1.4  # Specific heat ratio
    reduced_frequency: float = 0.0  # k = ωc/V (for unsteady analysis)
    piston_theory_order: int = 1  # Order of piston theory (1st or 2nd order)

    def __post_init__(self):
        if self.gamma <= 1.0:
            raise ValueError("Specific heat ratio must be > 1.0")
        if self.piston_theory_order not in [1, 2]:
            raise ValueError("Piston theory order must be 1 or 2")


@dataclass
class DoubletLatticeParameters:
    """Doublet lattice method parameters."""
    reduced_frequency: float = 0.0  # k = ωb/V (b = semi-chord)
    kernel_function: str = "W12"  # Kernel function type
    symmetry_xy: bool = False  # XY-plane symmetry
    symmetry_xz: bool = False  # XZ-plane symmetry
    antisymmetry_xy: bool = False  # XY-plane antisymmetry
    antisymmetry_xz: bool = False  # XZ-plane antisymmetry


@dataclass
class AerodynamicMesh:
    """Aerodynamic mesh parameters."""
    nx_aero: int  # Number of aerodynamic boxes in chordwise direction
    ny_aero: int  # Number of aerodynamic boxes in spanwise direction
    x_coords: List[float]  # X-coordinates of aerodynamic box corners
    y_coords: List[float]  # Y-coordinates of aerodynamic box corners
    z_coords: List[float]  # Z-coordinates of aerodynamic box corners

    def __post_init__(self):
        if self.nx_aero < 1:
            raise ValueError("Number of chordwise boxes must be >= 1")
        if self.ny_aero < 1:
            raise ValueError("Number of spanwise boxes must be >= 1")

        expected_points = (self.nx_aero + 1) * (self.ny_aero + 1)
        if len(self.x_coords) != expected_points:
            raise ValueError(f"Expected {expected_points} X-coordinates, got {len(self.x_coords)}")
        if len(self.y_coords) != expected_points:
            raise ValueError(f"Expected {expected_points} Y-coordinates, got {len(self.y_coords)}")
        if len(self.z_coords) != expected_points:
            raise ValueError(f"Expected {expected_points} Z-coordinates, got {len(self.z_coords)}")

    @property
    def total_boxes(self) -> int:
        """Total number of aerodynamic boxes."""
        return self.nx_aero * self.ny_aero


@dataclass
class AerodynamicElement:
    """Aerodynamic element definition."""
    element_id: int
    property_id: int
    element_type: str  # CAERO1, CAERO5, etc.
    corner_points: List[Tuple[float, float, float]]  # 4 corner points

    def __post_init__(self):
        if self.element_id <= 0:
            raise ValueError("Element ID must be positive")
        if len(self.corner_points) != 4:
            raise ValueError("Aerodynamic element must have 4 corner points")


class AerodynamicModel:
    """Complete aerodynamic model for NASTRAN flutter analysis."""

    def __init__(self, model_id: int, name: str):
        self.model_id = model_id
        self.name = name
        self.theory: AerodynamicTheory = AerodynamicTheory.PISTON_THEORY
        self.flow_conditions: Optional[FlowConditions] = None
        self.piston_params: Optional[PistonTheoryParameters] = None
        self.doublet_params: Optional[DoubletLatticeParameters] = None
        self.mesh: Optional[AerodynamicMesh] = None
        self.elements: List[AerodynamicElement] = []
        self.spline_points: List[Tuple[int, float, float, float]] = []  # (node_id, x, y, z)
        self._mesh_generated = False

    def set_flow_conditions(self, flow_conditions: FlowConditions):
        """Set flow conditions and automatically select appropriate theory."""
        self.flow_conditions = flow_conditions

        # Automatically select theory based on Mach number
        if flow_conditions.mach_number < 0.8:
            self.theory = AerodynamicTheory.DOUBLET_LATTICE
        else:
            self.theory = AerodynamicTheory.PISTON_THEORY

    def set_piston_theory_parameters(self, params: PistonTheoryParameters):
        """Set piston theory parameters."""
        self.piston_params = params
        if self.theory == AerodynamicTheory.DOUBLET_LATTICE:
            self.theory = AerodynamicTheory.PISTON_THEORY

    def set_doublet_lattice_parameters(self, params: DoubletLatticeParameters):
        """Set doublet lattice parameters."""
        self.doublet_params = params
        if self.theory == AerodynamicTheory.PISTON_THEORY:
            self.theory = AerodynamicTheory.DOUBLET_LATTICE

    def generate_aerodynamic_mesh(self, panel_length: float, panel_width: float,
                                 nx_aero: int, ny_aero: int, offset_z: float = 0.0) -> bool:
        """Generate aerodynamic mesh based on panel dimensions."""
        try:
            # Generate grid points
            x_coords = []
            y_coords = []
            z_coords = []

            dx = panel_length / nx_aero
            dy = panel_width / ny_aero

            for j in range(ny_aero + 1):
                for i in range(nx_aero + 1):
                    x = i * dx
                    y = j * dy
                    z = offset_z

                    x_coords.append(x)
                    y_coords.append(y)
                    z_coords.append(z)

            self.mesh = AerodynamicMesh(nx_aero, ny_aero, x_coords, y_coords, z_coords)

            # Generate aerodynamic elements
            self.elements.clear()
            element_id = 1

            for j in range(ny_aero):
                for i in range(nx_aero):
                    # Corner point indices
                    p1_idx = j * (nx_aero + 1) + i
                    p2_idx = p1_idx + 1
                    p3_idx = p2_idx + nx_aero + 1
                    p4_idx = p3_idx - 1

                    # Corner points
                    corner_points = [
                        (x_coords[p1_idx], y_coords[p1_idx], z_coords[p1_idx]),
                        (x_coords[p2_idx], y_coords[p2_idx], z_coords[p2_idx]),
                        (x_coords[p3_idx], y_coords[p3_idx], z_coords[p3_idx]),
                        (x_coords[p4_idx], y_coords[p4_idx], z_coords[p4_idx])
                    ]

                    element_type = "CAERO5" if self.theory == AerodynamicTheory.PISTON_THEORY else "CAERO1"
                    element = AerodynamicElement(element_id, 1, element_type, corner_points)
                    self.elements.append(element)
                    element_id += 1

            self._mesh_generated = True
            return True

        except Exception as e:
            self._mesh_generated = False
            raise RuntimeError(f"Failed to generate aerodynamic mesh: {str(e)}")

    def create_spline_connection(self, structural_nodes: List[Tuple[int, float, float, float]]):
        """Create spline connection between structural and aerodynamic models."""
        self.spline_points = structural_nodes.copy()

    def get_recommended_theory(self) -> AerodynamicTheory:
        """Get recommended aerodynamic theory based on flow conditions."""
        if not self.flow_conditions:
            return AerodynamicTheory.PISTON_THEORY

        mach = self.flow_conditions.mach_number

        if mach < 0.6:
            return AerodynamicTheory.DOUBLET_LATTICE
        elif mach > 1.5:
            return AerodynamicTheory.PISTON_THEORY
        else:
            # Transonic/low supersonic - Doublet Lattice works up to M=1.5
            return AerodynamicTheory.DOUBLET_LATTICE

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information summary."""
        theory_name = {
            AerodynamicTheory.PISTON_THEORY: "Piston Theory (CAERO5)",
            AerodynamicTheory.DOUBLET_LATTICE: "Doublet Lattice Method (CAERO1)",
            AerodynamicTheory.ZAERO: "ZAERO Advanced Aerodynamics"
        }.get(self.theory, "Unknown")

        flow_info = {}
        if self.flow_conditions:
            flow_info = {
                "mach_number": self.flow_conditions.mach_number,
                "dynamic_pressure": self.flow_conditions.dynamic_pressure,
                "flow_type": self.flow_conditions.flow_type.value,
                "flow_velocity": self.flow_conditions.flow_velocity,
                "altitude": self.flow_conditions.altitude,
                "temperature": self.flow_conditions.temperature
            }

        mesh_info = {}
        if self.mesh:
            mesh_info = {
                "nx_aero": self.mesh.nx_aero,
                "ny_aero": self.mesh.ny_aero,
                "total_boxes": self.mesh.total_boxes
            }

        return {
            "model_id": self.model_id,
            "name": self.name,
            "theory": theory_name,
            "flow_conditions": flow_info,
            "mesh": mesh_info,
            "elements_count": len(self.elements),
            "spline_points_count": len(self.spline_points),
            "mesh_generated": self._mesh_generated
        }

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the aerodynamic model."""
        errors = []

        if not self.flow_conditions:
            errors.append("Flow conditions not defined")

        if self.theory == AerodynamicTheory.PISTON_THEORY and not self.piston_params:
            errors.append("Piston theory parameters not defined")

        if self.theory == AerodynamicTheory.DOUBLET_LATTICE and not self.doublet_params:
            errors.append("Doublet lattice parameters not defined")

        if not self.mesh:
            errors.append("Aerodynamic mesh not generated")

        if not self.elements:
            errors.append("No aerodynamic elements defined")

        if not self.spline_points:
            errors.append("No spline connection points defined")

        # Validate theory selection against flow conditions
        if self.flow_conditions:
            recommended = self.get_recommended_theory()
            if self.theory != recommended:
                mach = self.flow_conditions.mach_number
                if mach < 0.6 and self.theory == AerodynamicTheory.PISTON_THEORY:
                    errors.append(f"Piston theory may not be accurate for M={mach:.2f}. Consider Doublet Lattice Method.")
                elif mach > 1.5 and self.theory == AerodynamicTheory.DOUBLET_LATTICE:
                    errors.append(f"Doublet Lattice Method may not be accurate for M={mach:.2f}. Consider Piston Theory.")

        return len(errors) == 0, errors

    def get_nastran_cards(self) -> List[str]:
        """Generate NASTRAN cards for the aerodynamic model."""
        cards = []

        if not self._mesh_generated:
            raise RuntimeError("Mesh not generated - cannot create NASTRAN cards")

        # AERO card for basic aerodynamic data
        if self.flow_conditions:
            aero_card = f"AERO    {self.model_id:8d}        {self.flow_conditions.mach_number:8.4f}{self.flow_conditions.dynamic_pressure:8.2E}"
            cards.append(aero_card)

        # CAERO cards for aerodynamic elements
        for element in self.elements:
            if element.element_type == "CAERO5":
                # Piston theory panel
                p1, p2, p3, p4 = element.corner_points
                caero_card = (f"CAERO5  {element.element_id:8d}{element.property_id:8d}"
                            f"{p1[0]:8.4f}{p1[1]:8.4f}{p1[2]:8.4f}"
                            f"{p2[0]:8.4f}{p2[1]:8.4f}{p2[2]:8.4f}")
                cards.append(caero_card)

                # Continuation card
                cont_card = (f"        {p3[0]:8.4f}{p3[1]:8.4f}{p3[2]:8.4f}"
                           f"{p4[0]:8.4f}{p4[1]:8.4f}{p4[2]:8.4f}")
                cards.append(cont_card)

            elif element.element_type == "CAERO1":
                # Doublet lattice panel
                p1, p2, p3, p4 = element.corner_points
                caero_card = (f"CAERO1  {element.element_id:8d}{element.property_id:8d}"
                            f"{self.mesh.nx_aero:8d}{self.mesh.ny_aero:8d}")
                cards.append(caero_card)

                # Coordinate data
                coord_card = (f"        {p1[0]:8.4f}{p1[1]:8.4f}{p1[2]:8.4f}"
                            f"{p2[0]:8.4f}{p2[1]:8.4f}{p2[2]:8.4f}")
                cards.append(coord_card)

                cont_card = (f"        {p3[0]:8.4f}{p3[1]:8.4f}{p3[2]:8.4f}"
                           f"{p4[0]:8.4f}{p4[1]:8.4f}{p4[2]:8.4f}")
                cards.append(cont_card)

        # PAERO cards for aerodynamic properties
        if self.theory == AerodynamicTheory.PISTON_THEORY and self.piston_params:
            paero_card = f"PAERO5  {1:8d}                {self.piston_params.gamma:8.4f}"
            cards.append(paero_card)
        elif self.theory == AerodynamicTheory.DOUBLET_LATTICE and self.doublet_params:
            paero_card = f"PAERO1  {1:8d}"
            cards.append(paero_card)

        return cards