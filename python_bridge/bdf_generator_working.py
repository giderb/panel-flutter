"""Robust NASTRAN BDF generator used by the GUI flutter workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional
from dataclasses import dataclass, field
import logging

from pyNastran.bdf.bdf import BDF
from pyNastran.bdf.case_control_deck import CaseControlDeck

logger = logging.getLogger(__name__)


@dataclass
class PanelConfig:
    """Panel configuration for BDF generation (lengths in mm)."""

    length: float
    width: float
    thickness: float
    nx: int
    ny: int
    material_id: int = 1
    property_id: int = 1


@dataclass
class MaterialConfig:
    """Material properties for BDF (SI units: mm-kg-s-N)."""

    youngs_modulus: float
    poissons_ratio: float
    density: float
    shear_modulus: Optional[float] = None
    material_id: int = 1


@dataclass
class AeroConfig:
    """Aerodynamic configuration for BDF (SI units: mm-kg-s-N)."""

    mach_number: float
    reference_velocity: float  # mm/s
    reference_chord: float  # mm
    reference_density: float  # kg/mm^3
    reduced_frequencies: List[float] = field(default_factory=list)
    velocities: List[float] = field(default_factory=list)  # mm/s


class WorkingBDFGenerator:
    """Create NASTRAN bulk data files ready for flutter analysis."""

    def __init__(self, output_dir: str = ".") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # High level API
    # ------------------------------------------------------------------
    def generate_bdf(
        self,
        panel: PanelConfig,
        material: MaterialConfig,
        aero: AeroConfig,
        boundary_conditions: str = "SSSS",
        n_modes: int = 10,
        output_filename: str = "flutter_analysis.bdf",
    ) -> str:
        """Generate a fully validated BDF file for SOL 145 flutter analysis."""

        self._validate_inputs(panel, material, aero, n_modes)

        bdf_model = BDF()
        bdf_model.sol = 145
        bdf_model.case_control_deck = self._build_case_control()
        self._add_global_parameters(bdf_model)
        self._add_material_and_property(bdf_model, panel, material)
        grid_ids = self._add_structural_model(bdf_model, panel)
        self._apply_boundary_conditions(bdf_model, panel, boundary_conditions, grid_ids)
        self._add_modal_extraction(bdf_model, n_modes)
        self._add_aero_model(bdf_model, panel, aero, grid_ids)
        self._add_flutter_cards(bdf_model, aero)

        filepath = self.output_dir / output_filename
        logger.debug("Writing BDF to %s", filepath)
        bdf_model.write_bdf(str(filepath), interspersed=False)
        logger.info("Generated BDF file: %s", filepath)
        return str(filepath)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate_inputs(
        self,
        panel: PanelConfig,
        material: MaterialConfig,
        aero: AeroConfig,
        n_modes: int,
    ) -> None:
        if panel.nx < 1 or panel.ny < 1:
            raise ValueError("Panel mesh must have at least 1 element in both directions")
        if panel.length <= 0 or panel.width <= 0:
            raise ValueError("Panel dimensions must be positive")
        if panel.thickness <= 0:
            raise ValueError("Panel thickness must be positive")
        if material.youngs_modulus <= 0 or material.density <= 0:
            raise ValueError("Material properties must be positive")
        if n_modes < 1:
            raise ValueError("At least one mode must be requested for eigenvalue extraction")
        if aero.reference_chord <= 0 or aero.reference_velocity <= 0:
            raise ValueError("Aerodynamic reference values must be positive")
        if aero.reference_density <= 0:
            raise ValueError("Aerodynamic reference density must be positive")

    def _build_case_control(self) -> CaseControlDeck:
        """Create a case control deck that requests flutter output."""

        case_control = [
            "TITLE = Panel Flutter Analysis",
            "ECHO = NONE",
            "SUBCASE 1",
            "    LABEL = Flutter Analysis",
            "    METHOD = 1",
            "    FMETHOD = 1",
            "    SPC = 1",
            "    FLUTTER = 1",
            "    DISPLACEMENT(PLOT) = ALL",
            "    SPCFORCES = ALL",
        ]
        return CaseControlDeck(case_control)

    def _add_global_parameters(self, model: BDF) -> None:
        model.add_param("POST", -2)
        model.add_param("COUPMASS", 1.0)
        model.add_param("GRDPNT", 0)

    def _add_material_and_property(self, model: BDF, panel: PanelConfig, material: MaterialConfig) -> None:
        shear_modulus = material.shear_modulus
        if shear_modulus is None:
            shear_modulus = material.youngs_modulus / (2.0 * (1.0 + material.poissons_ratio))
        model.add_mat1(
            material.material_id,
            material.youngs_modulus,
            shear_modulus,
            material.poissons_ratio,
            material.density,
        )
        model.add_pshell(panel.property_id, material.material_id, t=panel.thickness)

    def _add_structural_model(self, model: BDF, panel: PanelConfig) -> List[int]:
        grid_ids: List[int] = []
        dx = panel.length / panel.nx
        dy = panel.width / panel.ny
        node_id = 1
        for j in range(panel.ny + 1):
            for i in range(panel.nx + 1):
                x = i * dx
                y = j * dy
                model.add_grid(node_id, [x, y, 0.0])
                grid_ids.append(node_id)
                node_id += 1

        element_id = 1
        for j in range(panel.ny):
            for i in range(panel.nx):
                n1 = j * (panel.nx + 1) + i + 1
                n2 = n1 + 1
                n3 = n1 + panel.nx + 2
                n4 = n1 + panel.nx + 1
                model.add_cquad4(element_id, panel.property_id, [n1, n2, n3, n4])
                element_id += 1
        return grid_ids

    def _apply_boundary_conditions(
        self,
        model: BDF,
        panel: PanelConfig,
        boundary_conditions: str,
        grid_ids: List[int],
    ) -> None:
        if hasattr(boundary_conditions, "value"):
            bc_string = boundary_conditions.value
        else:
            bc_string = str(boundary_conditions or "SSSS")
        bc_string = bc_string.upper()
        if len(bc_string) != 4:
            raise ValueError("Boundary condition string must contain 4 characters (one per edge)")

        edge_nodes = self._collect_edge_nodes(panel)
        dof_map = {"C": "123456", "S": "3", "F": ""}
        dof_to_nodes: dict[str, set[int]] = {}
        for edge, code in zip(("bottom", "right", "top", "left"), bc_string):
            dofs = dof_map.get(code)
            if dofs is None:
                raise ValueError(f"Unsupported boundary condition code: {code}")
            if not dofs:
                continue
            dof_to_nodes.setdefault(dofs, set()).update(edge_nodes[edge])

        spc_id = 1
        for dof_string, nodes in dof_to_nodes.items():
            model.add_spc1(spc_id, dof_string, sorted(nodes))
            spc_id += 1

        # Remove rigid body motion by pinning in-plane DOF at reference nodes
        anchor = grid_ids[0]
        model.add_spc1(spc_id, "12", [anchor])
        spc_id += 1
        if len(grid_ids) > 1:
            model.add_spc1(spc_id, "2", [grid_ids[1]])
            spc_id += 1
        row_step = panel.nx + 1
        if len(grid_ids) > row_step:
            model.add_spc1(spc_id, "1", [grid_ids[row_step]])

    def _collect_edge_nodes(self, panel: PanelConfig) -> Dict[str, Iterable[int]]:
        bottom = [i + 1 for i in range(panel.nx + 1)]
        top = [panel.ny * (panel.nx + 1) + i + 1 for i in range(panel.nx + 1)]
        left = [j * (panel.nx + 1) + 1 for j in range(1, panel.ny)]
        right = [j * (panel.nx + 1) + panel.nx + 1 for j in range(1, panel.ny)]
        return {
            "bottom": bottom,
            "top": top,
            "left": left,
            "right": right,
        }

    def _add_modal_extraction(self, model: BDF, n_modes: int) -> None:
        model.add_eigrl(1, nd=n_modes, msglvl=0)

    def _add_aero_model(self, model: BDF, panel: PanelConfig, aero: AeroConfig, grid_ids: List[int]) -> None:
        model.add_aero(aero.reference_velocity, aero.reference_chord, aero.reference_density)
        model.add_paero1(1)
        model.add_caero1(
            1001,
            1,
            0,
            [0.0, 0.0, 0.0],
            panel.length,
            [0.0, panel.width, 0.0],
            panel.length,
            cp=0,
            nspan=panel.ny,
            nchord=panel.nx,
        )
        model.add_set1(1, grid_ids)
        model.add_spline1(1, 1001, 1, panel.nx * panel.ny, 1)

    def _add_flutter_cards(self, model: BDF, aero: AeroConfig) -> None:
        density_values = [1.0]
        mach_values = [aero.mach_number]
        velocity_values = self._prepare_velocity_list(aero.velocities)
        reduced_freqs = self._prepare_reduced_frequency_list(aero.reduced_frequencies)

        model.add_flfact(1, density_values)
        model.add_flfact(2, mach_values)
        model.add_flfact(3, velocity_values)
        model.add_flutter(1, "PK", 1, 2, 3, "L")
        model.add_mkaero1(mach_values, reduced_freqs)

    def _prepare_velocity_list(self, velocities: Iterable[float]) -> List[float]:
        values = [float(v) for v in velocities if float(v) > 0]
        if not values:
            # Default sweep from 500 m/s to 1500 m/s (converted to mm/s)
            values = [v * 1.0e5 for v in range(5, 16)]
        return sorted(values)

    def _prepare_reduced_frequency_list(self, reduced_freqs: Iterable[float]) -> List[float]:
        values = [float(k) for k in reduced_freqs if float(k) > 0]
        if not values:
            values = [0.001, 0.01, 0.05, 0.1, 0.2]
        return sorted(values)


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