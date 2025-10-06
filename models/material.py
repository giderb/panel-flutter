"""Material property models for panel flutter analysis."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class MaterialType(Enum):
    ISOTROPIC = "isotropic"
    ORTHOTROPIC = "orthotropic"
    COMPOSITE = "composite"
    SANDWICH = "sandwich"

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

@dataclass
class HoneycombCore:
    """Honeycomb core material properties."""
    name: str
    shear_modulus_lw: float  # Shear modulus in L-W plane (Pa)
    shear_modulus_lt: float  # Shear modulus in L-T plane (Pa)
    shear_modulus_wt: float  # Shear modulus in W-T plane (Pa)
    density: float  # kg/m³
    compressive_strength: Optional[float] = None  # Pa
    cell_size: Optional[float] = None  # mm
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "shear_modulus_lw": self.shear_modulus_lw,
            "shear_modulus_lt": self.shear_modulus_lt,
            "shear_modulus_wt": self.shear_modulus_wt,
            "density": self.density,
            "compressive_strength": self.compressive_strength,
            "cell_size": self.cell_size,
            "description": self.description
        }

@dataclass
class SandwichPanel:
    """
    Sandwich panel construction with face sheets and honeycomb core.

    Based on classical sandwich panel theory (Allen, 1969):
    - Face sheets carry bending loads
    - Core provides shear resistance and spacing
    - Total thickness = 2*t_face + t_core
    - Bending stiffness D = E_face * t_face * d² / (1-ν²) + E_face * t_face³ / [12(1-ν²)]
      where d = distance from neutral axis to face centroid
    """
    id: int
    name: str
    face_material: IsotropicMaterial  # Face sheet material
    face_thickness: float  # Face sheet thickness (mm)
    core_material: HoneycombCore  # Honeycomb core
    core_thickness: float  # Core thickness (mm)
    description: Optional[str] = None

    @property
    def total_thickness(self) -> float:
        """Total panel thickness (mm)."""
        return 2 * self.face_thickness + self.core_thickness

    @property
    def total_density(self) -> float:
        """
        Equivalent density (kg/m³).

        Returns mass per unit volume averaged over total thickness.
        """
        face_volume = 2 * self.face_thickness  # mm per unit area
        core_volume = self.core_thickness  # mm per unit area
        total_volume = self.total_thickness  # mm per unit area

        total_mass = (face_volume * self.face_material.density +
                     core_volume * self.core_material.density)

        return total_mass / total_volume

    @property
    def mass_per_area(self) -> float:
        """
        Mass per unit area (kg/m²).

        m = 2*ρ_face*t_face + ρ_core*t_core (converting mm to m)
        """
        return (2 * self.face_material.density * self.face_thickness * 1e-3 +
                self.core_material.density * self.core_thickness * 1e-3)

    def get_equivalent_properties(self) -> Dict[str, float]:
        """
        Calculate equivalent properties using classical sandwich theory.

        Returns:
            Dictionary with:
            - flexural_rigidity: D (N·m)
            - effective_youngs: E_eff (Pa)
            - shear_rigidity: Shear stiffness (N)
            - mass_per_area: Mass/area (kg/m²)
            - neutral_axis: Distance to neutral axis (mm)

        Reference: Allen, H.G. (1969). "Analysis and Design of Structural Sandwich Panels"
        """
        # Convert thicknesses to meters for calculations
        t_f = self.face_thickness * 1e-3  # m
        t_c = self.core_thickness * 1e-3  # m
        h = self.total_thickness * 1e-3  # m

        E_f = self.face_material.youngs_modulus  # Pa
        nu_f = self.face_material.poissons_ratio

        # Distance from neutral axis to face centroid
        d = (t_c + t_f) / 2

        # Bending stiffness (flexural rigidity) per unit width
        # D = (E_f * t_f * d²) / (1 - ν_f²) + (E_f * t_f³) / [12(1 - ν_f²)]
        # First term: bending of faces about their own neutral axis at distance d
        # Second term: local bending of face sheets
        D_faces = E_f * t_f * d**2 / (1 - nu_f**2)
        D_local = E_f * t_f**3 / (12 * (1 - nu_f**2))
        D_total = D_faces + D_local

        # Effective Young's modulus (for comparison with solid panel)
        # Based on: D = E_eff * h³ / [12(1 - ν²)]
        E_eff = 12 * D_total * (1 - nu_f**2) / h**3

        # Shear rigidity (approximate)
        # U = G_core * t_core (core shear dominates)
        U = self.core_material.shear_modulus_lw * t_c

        # Calculate weight saving directly (avoid recursion)
        m_sandwich = self.mass_per_area
        h_solid_cubed = 12 * D_total * (1 - nu_f**2) / E_f
        h_solid = h_solid_cubed ** (1/3)  # m
        m_solid = self.face_material.density * h_solid  # kg/m²
        weight_saving = (1 - m_sandwich / m_solid) * 100 if m_solid > 0 else 0.0

        # Calculate first mode frequency estimate for standard test panel (508x254 mm)
        # f_11 = (π²/2) × √(D/m) × √[(1/a)² + (1/b)²]
        import numpy as np
        a = 0.508  # m (standard test panel length)
        b = 0.254  # m (standard test panel width)
        freq_coeff = ((1/a)**2 + (1/b)**2)
        f_11_estimate = (np.pi**2 / 2) * np.sqrt(D_total / m_sandwich) * np.sqrt(freq_coeff)

        return {
            "flexural_rigidity": D_total,  # N·m
            "effective_youngs_modulus": E_eff,  # Pa
            "shear_rigidity": U,  # N
            "mass_per_area": self.mass_per_area,  # kg/m²
            "neutral_axis_offset": 0.0,  # Symmetric sandwich
            "face_thickness_m": t_f,  # m
            "core_thickness_m": t_c,  # m
            "total_thickness_m": h,  # m
            "face_youngs": E_f,  # Pa
            "face_poisson": nu_f,
            "core_shear": self.core_material.shear_modulus_lw,  # Pa
            "weight_saving": weight_saving,  # %
            "equivalent_solid_thickness_m": h_solid,  # m
            "first_mode_freq_estimate": f_11_estimate  # Hz (for 508x254mm panel)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": "sandwich",
            "id": self.id,
            "name": self.name,
            "face_material": self.face_material.to_dict(),
            "face_thickness": self.face_thickness,
            "core_material": self.core_material.to_dict(),
            "core_thickness": self.core_thickness,
            "total_thickness": self.total_thickness,
            "description": self.description,
            "equivalent_properties": self.get_equivalent_properties()
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

    @staticmethod
    def aluminum_honeycomb_5052() -> HoneycombCore:
        """Aluminum 5052 Honeycomb - 1/4" cell, 3.0 lb/ft³."""
        return HoneycombCore(
            name="Al 5052 Honeycomb 1/4\"-3.0",
            shear_modulus_lw=48.3e6,  # 48.3 MPa (7000 psi) - L-W plane
            shear_modulus_lt=27.6e6,  # 27.6 MPa (4000 psi) - L-T plane
            shear_modulus_wt=20.7e6,  # 20.7 MPa (3000 psi) - W-T plane
            density=48.0,  # 48 kg/m³ (3.0 lb/ft³)
            compressive_strength=1.38e6,  # 1.38 MPa (200 psi)
            cell_size=6.35,  # mm (1/4")
            description="Common aerospace aluminum honeycomb"
        )

    @staticmethod
    def aluminum_honeycomb_5056() -> HoneycombCore:
        """Aluminum 5056 Honeycomb - 3/16" cell, 4.5 lb/ft³."""
        return HoneycombCore(
            name="Al 5056 Honeycomb 3/16\"-4.5",
            shear_modulus_lw=89.6e6,  # 89.6 MPa (13000 psi)
            shear_modulus_lt=51.7e6,  # 51.7 MPa (7500 psi)
            shear_modulus_wt=41.4e6,  # 41.4 MPa (6000 psi)
            density=72.0,  # 72 kg/m³ (4.5 lb/ft³)
            compressive_strength=2.76e6,  # 2.76 MPa (400 psi)
            cell_size=4.76,  # mm (3/16")
            description="Higher density aluminum honeycomb for higher loads"
        )

    @staticmethod
    def nomex_honeycomb() -> HoneycombCore:
        """Nomex Honeycomb - 1/8" cell, 3.0 lb/ft³."""
        return HoneycombCore(
            name="Nomex Honeycomb 1/8\"-3.0",
            shear_modulus_lw=31.0e6,  # 31.0 MPa (4500 psi)
            shear_modulus_lt=24.1e6,  # 24.1 MPa (3500 psi)
            shear_modulus_wt=20.7e6,  # 20.7 MPa (3000 psi)
            density=48.0,  # 48 kg/m³ (3.0 lb/ft³)
            compressive_strength=0.69e6,  # 0.69 MPa (100 psi)
            cell_size=3.18,  # mm (1/8")
            description="Aramid fiber honeycomb, non-conductive"
        )

    @staticmethod
    def create_aluminum_sandwich() -> SandwichPanel:
        """Create typical aluminum sandwich panel for aerospace."""
        return SandwichPanel(
            id=1,
            name="Aluminum Sandwich Panel",
            face_material=PredefinedMaterials.aluminum_6061(),
            face_thickness=0.5,  # mm (0.020")
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7,  # mm (0.5")
            description="Typical aerospace sandwich: 0.020\" Al faces + 0.5\" honeycomb core"
        )

    @staticmethod
    def create_composite_sandwich() -> SandwichPanel:
        """Create composite face/honeycomb core sandwich panel."""
        # Use aluminum for face (composite would require OrthotropicMaterial support)
        return SandwichPanel(
            id=2,
            name="Composite Sandwich Panel",
            face_material=PredefinedMaterials.aluminum_6061(),
            face_thickness=0.76,  # mm (0.030")
            core_material=PredefinedMaterials.nomex_honeycomb(),
            core_thickness=19.1,  # mm (0.75")
            description="Thick core sandwich for high stiffness-to-weight"
        )

    @classmethod
    def get_all_honeycomb_cores(cls) -> List[HoneycombCore]:
        """Get all predefined honeycomb cores."""
        return [
            cls.aluminum_honeycomb_5052(),
            cls.aluminum_honeycomb_5056(),
            cls.nomex_honeycomb()
        ]

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
    elif material_type == "sandwich":
        # Deserialize face material
        face_data = data["face_material"]
        face_material = IsotropicMaterial(**{k: v for k, v in face_data.items() if k != "type"})

        # Deserialize core material
        core_data = data["core_material"]
        core_material = HoneycombCore(**core_data)

        return SandwichPanel(
            id=data["id"],
            name=data["name"],
            face_material=face_material,
            face_thickness=data["face_thickness"],
            core_material=core_material,
            core_thickness=data["core_thickness"],
            description=data.get("description")
        )
    else:
        raise ValueError(f"Unknown material type: {material_type}")