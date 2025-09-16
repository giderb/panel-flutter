"""Structural model definitions for NASTRAN panel flutter analysis."""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np


class BoundaryCondition(Enum):
    """Boundary condition types for panels."""
    SSSS = "SSSS"  # Simply supported on all four edges
    CCCC = "CCCC"  # Clamped on all four edges
    CFFF = "CFFF"  # Clamped-Free-Free-Free (cantilever)
    CFCF = "CFCF"  # Clamped-Free-Clamped-Free
    SCSC = "SCSC"  # Simply supported-Clamped-Simply supported-Clamped
    CUSTOM = "CUSTOM"  # User-defined boundary conditions


class ElementType(Enum):
    """NASTRAN element types for structural modeling."""
    CQUAD4 = "CQUAD4"  # 4-node quadrilateral shell element
    CQUAD8 = "CQUAD8"  # 8-node quadrilateral shell element
    CTRIA3 = "CTRIA3"  # 3-node triangular shell element
    CTRIA6 = "CTRIA6"  # 6-node triangular shell element


@dataclass
class PanelGeometry:
    """Panel geometry definition."""
    length: float  # Panel length (a) in meters
    width: float   # Panel width (b) in meters
    thickness: float  # Panel thickness in meters

    def __post_init__(self):
        if self.length <= 0:
            raise ValueError("Panel length must be positive")
        if self.width <= 0:
            raise ValueError("Panel width must be positive")
        if self.thickness <= 0:
            raise ValueError("Panel thickness must be positive")

    @property
    def aspect_ratio(self) -> float:
        """Calculate panel aspect ratio (length/width)."""
        return self.length / self.width

    @property
    def area(self) -> float:
        """Calculate panel area."""
        return self.length * self.width


@dataclass
class MeshParameters:
    """Mesh generation parameters."""
    nx: int  # Number of elements in x-direction
    ny: int  # Number of elements in y-direction
    element_type: ElementType = ElementType.CQUAD4

    def __post_init__(self):
        if self.nx < 1:
            raise ValueError("Number of elements in x-direction must be >= 1")
        if self.ny < 1:
            raise ValueError("Number of elements in y-direction must be >= 1")

    @property
    def total_elements(self) -> int:
        """Calculate total number of elements."""
        return self.nx * self.ny

    @property
    def total_nodes(self) -> int:
        """Calculate total number of nodes (for CQUAD4)."""
        if self.element_type == ElementType.CQUAD4:
            return (self.nx + 1) * (self.ny + 1)
        elif self.element_type == ElementType.CQUAD8:
            return (2 * self.nx + 1) * (2 * self.ny + 1)
        else:
            # Simplified estimation for triangular elements
            return (self.nx + 1) * (self.ny + 1)


@dataclass
class StructuralProperties:
    """Structural properties for shell elements."""
    property_id: int
    material_id: int
    membrane_thickness: Optional[float] = None
    membrane_material_id: Optional[int] = None
    bending_material_id: Optional[int] = None
    transverse_shear_thickness: Optional[float] = None
    membrane_bending_coupling_factor: float = 0.0
    transverse_shear_material_id: Optional[int] = None
    nonstructural_mass_per_unit_area: float = 0.0

    def __post_init__(self):
        if self.property_id <= 0:
            raise ValueError("Property ID must be positive")
        if self.material_id <= 0:
            raise ValueError("Material ID must be positive")


@dataclass
class NodeCoordinate:
    """Node coordinate definition."""
    node_id: int
    x: float
    y: float
    z: float = 0.0
    coordinate_system: int = 0


@dataclass
class Element:
    """Structural element definition."""
    element_id: int
    property_id: int
    element_type: ElementType
    node_ids: List[int]

    def __post_init__(self):
        if self.element_id <= 0:
            raise ValueError("Element ID must be positive")
        if self.property_id <= 0:
            raise ValueError("Property ID must be positive")

        # Validate node count based on element type
        expected_nodes = {
            ElementType.CQUAD4: 4,
            ElementType.CQUAD8: 8,
            ElementType.CTRIA3: 3,
            ElementType.CTRIA6: 6
        }

        if len(self.node_ids) != expected_nodes[self.element_type]:
            raise ValueError(f"{self.element_type.value} requires {expected_nodes[self.element_type]} nodes")


@dataclass
class BoundaryConstraint:
    """Boundary constraint definition."""
    node_id: int
    dof_constraints: str  # e.g., "123456" for all DOFs constrained
    coordinate_system: int = 0


class StructuralModel:
    """Complete structural model for NASTRAN analysis."""

    def __init__(self, model_id: int, name: str):
        self.model_id = model_id
        self.name = name
        self.geometry: Optional[PanelGeometry] = None
        self.mesh_params: Optional[MeshParameters] = None
        self.boundary_condition: BoundaryCondition = BoundaryCondition.SSSS
        self.properties: List[StructuralProperties] = []
        self.materials: List[Any] = []  # Material objects from material.py
        self.nodes: List[NodeCoordinate] = []
        self.elements: List[Element] = []
        self.constraints: List[BoundaryConstraint] = []
        self._mesh_generated = False

    def set_geometry(self, geometry: PanelGeometry):
        """Set panel geometry."""
        self.geometry = geometry
        self._mesh_generated = False

    def set_mesh_parameters(self, mesh_params: MeshParameters):
        """Set mesh parameters."""
        self.mesh_params = mesh_params
        self._mesh_generated = False

    def add_property(self, prop: StructuralProperties):
        """Add structural property."""
        self.properties.append(prop)

    def add_material(self, material: Any):
        """Add material to the model."""
        self.materials.append(material)

    def get_material(self, material_id: int = None):
        """Get material by ID, or return first material if no ID specified."""
        if material_id is None:
            return self.materials[0] if self.materials else None

        for material in self.materials:
            if hasattr(material, 'id') and material.id == material_id:
                return material
        return None

    def generate_mesh(self) -> bool:
        """Generate structural mesh based on geometry and parameters."""
        if not self.geometry or not self.mesh_params:
            raise ValueError("Geometry and mesh parameters must be set before generating mesh")

        self.nodes.clear()
        self.elements.clear()

        # Generate nodes
        dx = self.geometry.length / self.mesh_params.nx
        dy = self.geometry.width / self.mesh_params.ny

        node_id = 1
        for j in range(self.mesh_params.ny + 1):
            for i in range(self.mesh_params.nx + 1):
                x = i * dx
                y = j * dy
                z = 0.0
                self.nodes.append(NodeCoordinate(node_id, x, y, z))
                node_id += 1

        # Generate elements (CQUAD4)
        if self.mesh_params.element_type == ElementType.CQUAD4:
            element_id = 1
            for j in range(self.mesh_params.ny):
                for i in range(self.mesh_params.nx):
                    # Node connectivity for CQUAD4
                    n1 = j * (self.mesh_params.nx + 1) + i + 1
                    n2 = n1 + 1
                    n3 = n2 + self.mesh_params.nx + 1
                    n4 = n3 - 1

                    node_ids = [n1, n2, n3, n4]
                    prop_id = self.properties[0].property_id if self.properties else 1

                    element = Element(element_id, prop_id, ElementType.CQUAD4, node_ids)
                    self.elements.append(element)
                    element_id += 1

        # Generate boundary constraints based on boundary condition
        self._generate_boundary_constraints()

        self._mesh_generated = True
        return True

    def _generate_boundary_constraints(self):
        """Generate boundary constraints based on boundary condition type."""
        self.constraints.clear()

        if not self.mesh_params:
            return

        nx, ny = self.mesh_params.nx, self.mesh_params.ny

        if self.boundary_condition == BoundaryCondition.SSSS:
            # Simply supported: constrain z-translation on all edges
            dof_constraint = "3"

            # Bottom edge (y=0)
            for i in range(nx + 1):
                node_id = i + 1
                self.constraints.append(BoundaryConstraint(node_id, dof_constraint))

            # Top edge (y=width)
            for i in range(nx + 1):
                node_id = ny * (nx + 1) + i + 1
                self.constraints.append(BoundaryConstraint(node_id, dof_constraint))

            # Left edge (x=0)
            for j in range(1, ny):
                node_id = j * (nx + 1) + 1
                self.constraints.append(BoundaryConstraint(node_id, dof_constraint))

            # Right edge (x=length)
            for j in range(1, ny):
                node_id = j * (nx + 1) + nx + 1
                self.constraints.append(BoundaryConstraint(node_id, dof_constraint))

        elif self.boundary_condition == BoundaryCondition.CCCC:
            # Clamped: constrain all translations and rotations on all edges
            dof_constraint = "123456"

            # Apply to all edge nodes
            edge_nodes = set()

            # Bottom and top edges
            for i in range(nx + 1):
                edge_nodes.add(i + 1)  # Bottom
                edge_nodes.add(ny * (nx + 1) + i + 1)  # Top

            # Left and right edges
            for j in range(ny + 1):
                edge_nodes.add(j * (nx + 1) + 1)  # Left
                edge_nodes.add(j * (nx + 1) + nx + 1)  # Right

            for node_id in edge_nodes:
                self.constraints.append(BoundaryConstraint(node_id, dof_constraint))

        elif self.boundary_condition == BoundaryCondition.CFFF:
            # Cantilever: clamped at x=0, free elsewhere
            dof_constraint = "123456"

            # Left edge only (x=0)
            for j in range(ny + 1):
                node_id = j * (nx + 1) + 1
                self.constraints.append(BoundaryConstraint(node_id, dof_constraint))

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information summary."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "geometry": {
                "length": self.geometry.length if self.geometry else None,
                "width": self.geometry.width if self.geometry else None,
                "thickness": self.geometry.thickness if self.geometry else None,
                "aspect_ratio": self.geometry.aspect_ratio if self.geometry else None,
                "area": self.geometry.area if self.geometry else None
            },
            "mesh": {
                "nx": self.mesh_params.nx if self.mesh_params else None,
                "ny": self.mesh_params.ny if self.mesh_params else None,
                "element_type": self.mesh_params.element_type.value if self.mesh_params else None,
                "total_elements": self.mesh_params.total_elements if self.mesh_params else None,
                "total_nodes": self.mesh_params.total_nodes if self.mesh_params else None
            },
            "boundary_condition": self.boundary_condition.value,
            "properties_count": len(self.properties),
            "nodes_count": len(self.nodes),
            "elements_count": len(self.elements),
            "constraints_count": len(self.constraints),
            "mesh_generated": self._mesh_generated
        }

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the structural model."""
        errors = []

        if not self.geometry:
            errors.append("Panel geometry not defined")

        if not self.mesh_params:
            errors.append("Mesh parameters not defined")

        if not self.properties:
            errors.append("No structural properties defined")

        if not self._mesh_generated:
            errors.append("Mesh not generated")

        if self._mesh_generated:
            if not self.nodes:
                errors.append("No nodes generated")

            if not self.elements:
                errors.append("No elements generated")

            # Validate element node references
            node_ids = {node.node_id for node in self.nodes}
            for element in self.elements:
                for node_id in element.node_ids:
                    if node_id not in node_ids:
                        errors.append(f"Element {element.element_id} references non-existent node {node_id}")

        return len(errors) == 0, errors