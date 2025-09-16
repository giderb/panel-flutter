"""Material property models for panel flutter analysis."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class MaterialType(Enum):
    ISOTROPIC = "isotropic"
    ORTHOTROPIC = "orthotropic"
    COMPOSITE = "composite"

@dataclass
class IsotropicMaterial:
    """Isotropic material properties."""
    id: int
    name: str
    youngs_modulus: float  # Pa
    poissons_ratio: float
    shear_modulus: float  # Pa
    density: float  # kg/m³
    thermal_expansion: Optional[float] = None  # 1/K
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": "isotropic",
            "id": self.id,
            "name": self.name,
            "youngs_modulus": self.youngs_modulus,
            "poissons_ratio": self.poissons_ratio,
            "shear_modulus": self.shear_modulus,
            "density": self.density,
            "thermal_expansion": self.thermal_expansion,
            "description": self.description
        }

@dataclass
class OrthotropicMaterial:
    """Orthotropic material properties."""
    id: int
    name: str
    e1: float  # Young's modulus in direction 1 (Pa)
    e2: float  # Young's modulus in direction 2 (Pa)
    nu12: float  # Poisson's ratio 12
    g12: float  # Shear modulus 12 (Pa)
    density: float  # kg/m³
    alpha1: Optional[float] = None  # Thermal expansion 1 (1/K)
    alpha2: Optional[float] = None  # Thermal expansion 2 (1/K)
    g1z: Optional[float] = None  # Out-of-plane shear modulus 1z (Pa)
    g2z: Optional[float] = None  # Out-of-plane shear modulus 2z (Pa)
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": "orthotropic",
            "id": self.id,
            "name": self.name,
            "e1": self.e1,
            "e2": self.e2,
            "nu12": self.nu12,
            "g12": self.g12,
            "density": self.density,
            "alpha1": self.alpha1,
            "alpha2": self.alpha2,
            "g1z": self.g1z,
            "g2z": self.g2z,
            "description": self.description
        }

@dataclass
class CompositeLamina:
    """Individual lamina in a composite laminate."""
    id: int
    material: OrthotropicMaterial
    thickness: float  # mm
    orientation: float  # degrees

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "material": self.material.to_dict(),
            "thickness": self.thickness,
            "orientation": self.orientation
        }

@dataclass
class CompositeLaminate:
    """Composite laminate definition."""
    id: int
    name: str
    laminas: List[CompositeLamina]
    description: Optional[str] = None

    @property
    def total_thickness(self) -> float:
        """Calculate total laminate thickness."""
        return sum(lamina.thickness for lamina in self.laminas)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": "composite",
            "id": self.id,
            "name": self.name,
            "laminas": [lamina.to_dict() for lamina in self.laminas],
            "total_thickness": self.total_thickness,
            "description": self.description
        }

class PredefinedMaterials:
    """Predefined aerospace materials library."""

    @staticmethod
    def aluminum_6061() -> IsotropicMaterial:
        """Aluminum 6061-T6."""
        return IsotropicMaterial(
            id=1,
            name="Aluminum 6061-T6",
            youngs_modulus=71.7e9,  # 71.7 GPa
            poissons_ratio=0.33,
            shear_modulus=26.9e9,  # 26.9 GPa
            density=2810,  # kg/m³
            thermal_expansion=21e-6,  # 1/K
            description="Common aerospace aluminum alloy"
        )

    @staticmethod
    def steel_4130() -> IsotropicMaterial:
        """Steel 4130."""
        return IsotropicMaterial(
            id=2,
            name="Steel 4130",
            youngs_modulus=207e9,  # 207 GPa
            poissons_ratio=0.30,
            shear_modulus=80e9,  # 80 GPa
            density=7850,  # kg/m³
            thermal_expansion=12.3e-6,  # 1/K
            description="High-strength low-alloy steel"
        )

    @staticmethod
    def titanium_6al4v() -> IsotropicMaterial:
        """Titanium Ti-6Al-4V."""
        return IsotropicMaterial(
            id=3,
            name="Titanium Ti-6Al-4V",
            youngs_modulus=113.8e9,  # 113.8 GPa
            poissons_ratio=0.32,
            shear_modulus=44e9,  # 44 GPa
            density=4430,  # kg/m³
            thermal_expansion=8.6e-6,  # 1/K
            description="Common aerospace titanium alloy"
        )

    @staticmethod
    def carbon_fiber_epoxy() -> OrthotropicMaterial:
        """Carbon Fiber/Epoxy (IM7/8552)."""
        return OrthotropicMaterial(
            id=4,
            name="Carbon Fiber/Epoxy (IM7/8552)",
            e1=171e9,  # 171 GPa
            e2=9.08e9,  # 9.08 GPa
            nu12=0.32,
            g12=5.29e9,  # 5.29 GPa
            density=1570,  # kg/m³
            alpha1=-0.5e-6,  # 1/K
            alpha2=28.1e-6,  # 1/K
            description="Unidirectional carbon fiber composite"
        )

    @staticmethod
    def glass_epoxy() -> OrthotropicMaterial:
        """E-Glass/Epoxy."""
        return OrthotropicMaterial(
            id=5,
            name="E-Glass/Epoxy",
            e1=39.0e9,  # 39.0 GPa
            e2=8.6e9,  # 8.6 GPa
            nu12=0.28,
            g12=3.8e9,  # 3.8 GPa
            density=1970,  # kg/m³
            alpha1=7.0e-6,  # 1/K
            alpha2=21.0e-6,  # 1/K
            description="Unidirectional glass fiber composite"
        )

    @classmethod
    def get_all_isotropic(cls) -> List[IsotropicMaterial]:
        """Get all predefined isotropic materials."""
        return [
            cls.aluminum_6061(),
            cls.steel_4130(),
            cls.titanium_6al4v()
        ]

    @classmethod
    def get_all_orthotropic(cls) -> List[OrthotropicMaterial]:
        """Get all predefined orthotropic materials."""
        return [
            cls.carbon_fiber_epoxy(),
            cls.glass_epoxy()
        ]

    @classmethod
    def create_example_composite() -> CompositeLaminate:
        """Create an example composite laminate."""
        carbon_fiber = PredefinedMaterials.carbon_fiber_epoxy()

        laminas = [
            CompositeLamina(1, carbon_fiber, 0.125, 0),      # 0° ply
            CompositeLamina(2, carbon_fiber, 0.125, 45),     # 45° ply
            CompositeLamina(3, carbon_fiber, 0.125, -45),    # -45° ply
            CompositeLamina(4, carbon_fiber, 0.125, 90),     # 90° ply
            CompositeLamina(5, carbon_fiber, 0.125, 90),     # 90° ply
            CompositeLamina(6, carbon_fiber, 0.125, -45),    # -45° ply
            CompositeLamina(7, carbon_fiber, 0.125, 45),     # 45° ply
            CompositeLamina(8, carbon_fiber, 0.125, 0),      # 0° ply
        ]

        return CompositeLaminate(
            id=1,
            name="Carbon/Epoxy [0/45/-45/90]s",
            laminas=laminas,
            description="Symmetric quasi-isotropic laminate"
        )

def material_from_dict(data: Dict[str, Any]):
    """Create material object from dictionary."""
    material_type = data.get("type", "isotropic")

    if material_type == "isotropic":
        return IsotropicMaterial(**{k: v for k, v in data.items() if k != "type"})
    elif material_type == "orthotropic":
        return OrthotropicMaterial(**{k: v for k, v in data.items() if k != "type"})
    elif material_type == "composite":
        laminas = [
            CompositeLamina(
                id=lamina_data["id"],
                material=OrthotropicMaterial(**{k: v for k, v in lamina_data["material"].items() if k != "type"}),
                thickness=lamina_data["thickness"],
                orientation=lamina_data["orientation"]
            )
            for lamina_data in data["laminas"]
        ]
        return CompositeLaminate(
            id=data["id"],
            name=data["name"],
            laminas=laminas,
            description=data.get("description")
        )
    else:
        raise ValueError(f"Unknown material type: {material_type}")