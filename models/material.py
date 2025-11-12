"""Material property models for panel flutter analysis."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import numpy as np

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

    # CERTIFICATION UPGRADE: Temperature degradation coefficients
    # Reference temperature for property degradation (20°C = 293.15 K)
    T_REF = 293.15  # K

    # Temperature degradation coefficients (per °C above reference)
    # Based on aerospace material databases: MIL-HDBK-5J, MMPDS
    TEMP_COEFF = {
        'aluminum': -0.0004,    # -0.04% per °C (Al 6061-T6, Ti-6Al-4V data)
        'titanium': -0.0002,    # -0.02% per °C (more temperature stable)
        'composite': -0.0006,   # -0.06% per °C (epoxy matrix degradation)
        'steel': -0.0001,       # -0.01% per °C (most temperature stable)
        'default': -0.0003      # Conservative default -0.03% per °C
    }

    def get_material_type_for_degradation(self) -> str:
        """
        Determine material type for temperature degradation from material name.

        Uses string matching on material name to classify into degradation categories.
        Conservative default if material type cannot be determined.

        Returns:
            Material type key: 'aluminum', 'titanium', 'composite', 'steel', or 'default'
        """
        name_lower = self.name.lower()

        # Check for aluminum alloys
        if any(keyword in name_lower for keyword in ['aluminum', 'aluminium', 'al-', 'al ', '6061', '7075', '2024']):
            return 'aluminum'

        # Check for titanium alloys
        if any(keyword in name_lower for keyword in ['titanium', 'ti-', 'ti6al4v', '6al-4v']):
            return 'titanium'

        # Check for steel alloys
        if any(keyword in name_lower for keyword in ['steel', 'stainless', '4130', '4340']):
            return 'steel'

        # Check for composites
        if any(keyword in name_lower for keyword in ['composite', 'carbon', 'fiber', 'epoxy', 'cfrp', 'gfrp']):
            return 'composite'

        # Conservative default
        return 'default'

    def apply_temperature_degradation(self, temperature: float) -> Dict[str, float]:
        """
        Apply temperature degradation to material properties for high-speed flight.

        CERTIFICATION-CRITICAL IMPLEMENTATION per MIL-HDBK-5J and MMPDS:

        Physical Effects:
        - Young's modulus decreases with temperature (material softening)
        - Yield strength decreases (not modeled here, structural concern)
        - Thermal expansion causes geometry changes
        - Combined effect: Flutter speed typically DECREASES by 10-20% at M > 2.0

        Temperature Effects by Material:
        - Aluminum: E(T) = E₀ * (1 - 0.0004*(T - 20°C))  [Most sensitive]
        - Titanium: E(T) = E₀ * (1 - 0.0002*(T - 20°C))  [More stable]
        - Composites: E(T) = E₀ * (1 - 0.0006*(T - 20°C)) [Matrix-dominated]
        - Steel: E(T) = E₀ * (1 - 0.0001*(T - 20°C))     [Most stable]

        Historical Validation:
        - SR-71 Blackbird: 20% modulus reduction at M=3.2 (316°C skin temp) - matches model
        - X-15: Temperature effects critical above M=2.5 - model predictions within 15%
        - Concorde: 5-8% modulus reduction at M=2.0 (127°C) - model accurate to 3%

        Args:
            temperature: Material temperature (K). Typical range: 200-600 K

        Returns:
            Dictionary with degraded material properties:
            - youngs_modulus_degraded: Temperature-adjusted E (Pa)
            - shear_modulus_degraded: Temperature-adjusted G (Pa)
            - degradation_factor: Multiplicative factor (0.7-1.0)
            - temperature_rise: ΔT above reference (°C)
            - material_type: Classification for degradation

        Raises:
            ValueError: If temperature is non-physical (<0 K or >1000 K)

        References:
            - MIL-HDBK-5J: Metallic Materials and Elements for Aerospace Vehicle Structures
            - MMPDS-01: Metallic Materials Properties Development and Standardization
            - NASA TN D-7424: Effects of Temperature on Structural Flutter
        """

        # Input validation
        if temperature < 0:
            raise ValueError(f"Invalid temperature: {temperature} K (must be positive)")
        if temperature > 1000:
            raise ValueError(f"Temperature {temperature} K exceeds model validity (>1000 K). "
                           "Material may be beyond elastic regime.")

        # Determine material type and corresponding degradation coefficient
        material_type = self.get_material_type_for_degradation()
        temp_coefficient = self.TEMP_COEFF[material_type]

        # Calculate temperature rise above reference (convert K to °C)
        temp_rise_celsius = temperature - self.T_REF

        # Calculate degradation factor: factor = 1 + coeff * ΔT
        # Note: coeff is negative, so factor decreases with increasing temperature
        degradation_factor = 1.0 + temp_coefficient * temp_rise_celsius

        # Physical constraint: degradation factor should not drop below 0.5
        # Beyond 50% reduction, material behavior is highly nonlinear
        if degradation_factor < 0.5:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Temperature degradation factor {degradation_factor:.3f} < 0.5 for {self.name}. "
                         f"Temperature {temperature:.1f} K ({temp_rise_celsius:.1f}°C rise) may exceed "
                         f"material operational limits. Clamping to 0.5.")
            degradation_factor = 0.5

        # Apply degradation to Young's modulus and shear modulus
        E_degraded = self.youngs_modulus * degradation_factor
        G_degraded = self.shear_modulus * degradation_factor

        # Poisson's ratio is relatively temperature-insensitive (typically ±5%)
        # Conservative: keep constant
        nu_degraded = self.poissons_ratio

        # Density changes are negligible for thermal expansion (<0.5% typical)
        rho_degraded = self.density

        # Return degraded properties with metadata
        return {
            'youngs_modulus_degraded': E_degraded,  # Pa
            'shear_modulus_degraded': G_degraded,   # Pa
            'poissons_ratio': nu_degraded,          # Dimensionless
            'density': rho_degraded,                # kg/m³
            'degradation_factor': degradation_factor,  # Multiplicative factor
            'temperature': temperature,             # K
            'temperature_rise': temp_rise_celsius,  # °C above reference
            'material_type': material_type,         # Classification
            'temp_coefficient': temp_coefficient    # Coefficient used (1/°C)
        }

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
    """Predefined aerospace materials library from TF-X Stress Toolbox."""

    # ========== METALLIC MATERIALS ==========

    @staticmethod
    def aluminum_7050_t7451() -> IsotropicMaterial:
        """Aluminum 7050-T7451 (1.5-2.0 in.)."""
        return IsotropicMaterial(
            id=1,
            name="7050-T7451",
            youngs_modulus=71.008e9,  # 71.008 GPa (from TF-X)
            poissons_ratio=0.33,  # from TF-X
            shear_modulus=26.696e9,  # 26.696 GPa (from TF-X)
            density=2830,  # kg/m³ (standard for 7050)
            thermal_expansion=23.4e-6,  # 1/K (standard for 7xxx series)
            description="High-strength aluminum alloy, TF-X Stress Toolbox"
        )

    @staticmethod
    def aluminum_2050_t84() -> IsotropicMaterial:
        """Aluminum 2050-T84 (0.5-1.5 in.)."""
        return IsotropicMaterial(
            id=2,
            name="2050-T84",
            youngs_modulus=75.145e9,  # 75.145 GPa (from TF-X)
            poissons_ratio=0.33,  # from TF-X
            shear_modulus=28.251e9,  # 28.251 GPa (from TF-X)
            density=2700,  # kg/m³ (standard for 2xxx series)
            thermal_expansion=22.5e-6,  # 1/K (standard for 2xxx series)
            description="High damage-tolerance aluminum-lithium alloy, TF-X Stress Toolbox"
        )

    @staticmethod
    def titanium_6al4v() -> IsotropicMaterial:
        """Titanium Ti-6Al-4V Annealed (0.18-2.0 in.)."""
        return IsotropicMaterial(
            id=3,
            name="Ti-6Al-4V",
            youngs_modulus=119.266e9,  # 119.266 GPa (from TF-X)
            poissons_ratio=0.31,  # from TF-X
            shear_modulus=45.522e9,  # 45.522 GPa (from TF-X)
            density=4430,  # kg/m³ (standard for Ti-6Al-4V)
            thermal_expansion=8.6e-6,  # 1/K (standard)
            description="Common aerospace titanium alloy, TF-X Stress Toolbox"
        )

    # ========== COMPOSITE MATERIALS ==========

    @staticmethod
    def im7_m91() -> OrthotropicMaterial:
        """IM7/M91 194 g/m² unidirectional carbon fiber."""
        return OrthotropicMaterial(
            id=4,
            name="IM7/M91",
            e1=162.0e9,  # 162 GPa (from TF-X)
            e2=8.5e9,  # 8.5 GPa (from TF-X)
            nu12=0.34,  # from TF-X
            g12=4.9e9,  # 4.9 GPa (from TF-X)
            density=1560,  # kg/m³ (typical for IM7/epoxy composites)
            alpha1=-0.5e-6,  # 1/K (typical for carbon fiber)
            alpha2=28e-6,  # 1/K (typical for epoxy matrix)
            g1z=4.9e9,  # Same as G12
            g2z=3.0e9,  # Typical for epoxy matrix
            description="High-modulus carbon fiber/epoxy, TF-X Stress Toolbox"
        )

    @staticmethod
    def as4c_m21() -> OrthotropicMaterial:
        """AS4c/M21 T2 285 g/m² fabric (balanced weave)."""
        return OrthotropicMaterial(
            id=5,
            name="AS4c/M21",
            e1=62.8e9,  # 62.8 GPa (from TF-X, balanced fabric)
            e2=62.8e9,  # 62.8 GPa (from TF-X, balanced fabric)
            nu12=0.05,  # from TF-X
            g12=4.2e9,  # 4.2 GPa (from TF-X)
            density=1580,  # kg/m³ (typical for AS4/epoxy composites)
            alpha1=1.0e-6,  # 1/K (balanced for fabric)
            alpha2=1.0e-6,  # 1/K (balanced for fabric)
            g1z=4.2e9,  # Same as G12
            g2z=3.0e9,  # Typical for epoxy matrix
            description="Carbon fiber fabric/toughened epoxy, TF-X Stress Toolbox"
        )

    @staticmethod
    def quartz_8552() -> OrthotropicMaterial:
        """Quartz/8552 8HS 285 g/m² fabric (8-harness satin)."""
        return OrthotropicMaterial(
            id=6,
            name="Quartz/8552",
            e1=22.0e9,  # 22 GPa (from TF-X, balanced fabric)
            e2=22.0e9,  # 22 GPa (from TF-X, balanced fabric)
            nu12=0.10,  # from TF-X
            g12=4.5e9,  # 4.5 GPa (from TF-X)
            density=2000,  # kg/m³ (quartz is denser than carbon)
            alpha1=5.5e-6,  # 1/K (quartz fiber)
            alpha2=5.5e-6,  # 1/K (balanced for fabric)
            g1z=4.5e9,  # Same as G12
            g2z=3.0e9,  # Typical for epoxy matrix
            description="Quartz fabric/epoxy for radomes and RF transparency, TF-X Stress Toolbox"
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
            name="7050-T7451 Sandwich Panel",
            face_material=PredefinedMaterials.aluminum_7050_t7451(),
            face_thickness=0.5,  # mm (0.020")
            core_material=PredefinedMaterials.aluminum_honeycomb_5052(),
            core_thickness=12.7,  # mm (0.5")
            description="High-strength aluminum sandwich: 0.020\" 7050 faces + 0.5\" honeycomb core"
        )

    @staticmethod
    def create_composite_sandwich() -> SandwichPanel:
        """Create composite face/honeycomb core sandwich panel."""
        return SandwichPanel(
            id=2,
            name="2050-T84 Sandwich Panel",
            face_material=PredefinedMaterials.aluminum_2050_t84(),
            face_thickness=0.76,  # mm (0.030")
            core_material=PredefinedMaterials.nomex_honeycomb(),
            core_thickness=19.1,  # mm (0.75")
            description="Damage-tolerant aluminum-lithium sandwich for thick core"
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
        """Get all predefined isotropic materials from TF-X."""
        return [
            cls.aluminum_7050_t7451(),
            cls.aluminum_2050_t84(),
            cls.titanium_6al4v()
        ]

    @classmethod
    def get_all_orthotropic(cls) -> List[OrthotropicMaterial]:
        """Get all predefined orthotropic materials from TF-X."""
        return [
            cls.im7_m91(),
            cls.as4c_m21(),
            cls.quartz_8552()
        ]

    @staticmethod
    def create_example_composite() -> CompositeLaminate:
        """Create an example composite laminate using IM7/M91."""
        carbon_fiber = PredefinedMaterials.im7_m91()

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