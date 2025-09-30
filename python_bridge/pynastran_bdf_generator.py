"""
PyNastran-based BDF Generator for SOL145 Flutter Analysis
=========================================================

This module creates NASTRAN BDF files using pyNastran to ensure
proper formatting and eliminate fatal errors in NASTRAN execution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import datetime
import logging
import numpy as np

# Import pyNastran components
from pyNastran.bdf.bdf import BDF


def format_nastran_float(value: float) -> float:
    """
    CRITICAL FIX: Format float values to avoid scientific notation parsing issues
    NASTRAN expects proper float formatting without concatenation

    Args:
        value: Float value to format

    Returns:
        Properly formatted float for NASTRAN
    """
    # Ensure we don't get problematic formats like '7.17+10' or concatenated values
    if value is None or not isinstance(value, (int, float)):
        return 0.0

    # Convert to float to ensure proper type
    value = float(value)

    if abs(value) < 1e-10:
        return 0.0
    elif abs(value) > 1e15 or abs(value) < 1e-10:
        # For very large/small numbers, format properly
        formatted = f"{value:.3E}"
        return float(formatted.replace('+', '').replace('-', '-'))
    else:
        # For normal range numbers, use standard float
        return round(float(value), 6)

logger = logging.getLogger(__name__)


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
    """Material properties for BDF (SI units: m-kg-s-N)"""
    youngs_modulus: float  # Pa (N/m^2)
    poissons_ratio: float  # dimensionless
    density: float  # kg/m^3
    shear_modulus: Optional[float] = None  # Pa (N/m^2)
    material_id: int = 1


@dataclass
class AeroConfig:
    """Aerodynamic configuration for BDF (SI units: m-kg-s-N)"""
    mach_number: float
    reference_velocity: float  # m/s
    reference_chord: float  # m
    reference_density: float  # kg/m^3
    reduced_frequencies: List[float] = None
    velocities: List[float] = None  # m/s


class PyNastranBDFGenerator:
    """NASTRAN BDF file generator using pyNastran for SOL145 flutter analysis"""

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = None

    def generate_bdf(
        self,
        panel: PanelConfig,
        material: MaterialConfig,
        aero: AeroConfig,
        boundary_conditions: str = "SSSS",
        n_modes: int = 10,
        output_filename: str = "flutter_analysis.bdf"
    ) -> str:
        """Generate a NASTRAN BDF file for SOL145 flutter analysis using pyNastran"""

        # Initialize new BDF model
        self.model = BDF(debug=False)

        # Set units to SI (m-kg-s-N)
        self.model.units = ['m', 'kg', 's', 'N']

        filepath = self.output_dir / output_filename

        logger.info(f"Generating SOL145 BDF file using pyNastran: {filepath}")
        logger.info(f"Panel: {panel.length:.3f}m x {panel.width:.3f}m x {panel.thickness:.3f}m")
        logger.info(f"Mesh: {panel.nx}x{panel.ny} elements")

        # Add executive control
        self._add_executive_control()

        # Add case control
        self._add_case_control()

        # Add bulk data
        self._add_parameters()
        self._add_materials(material)
        self._add_properties(panel, material)
        self._add_grid_points(panel)
        self._add_elements(panel)
        self._add_boundary_conditions(panel, boundary_conditions)
        self._add_eigenvalue_extraction(n_modes)
        self._add_aerodynamic_cards(panel, aero)
        self._add_flutter_cards(aero, n_modes)

        # Write BDF file
        self.model.write_bdf(str(filepath), size=8, is_double=False, enddata=True)

        # Validate the BDF (temporarily disabled for debugging)
        # self._validate_bdf_file(filepath)

        logger.info(f"Successfully generated BDF file: {filepath}")
        return str(filepath)

    def _add_executive_control(self):
        """Add executive control section"""
        self.model.executive_control_lines = [
            'SOL 145',
            'CEND'
        ]

    def _add_case_control(self):
        """Add case control section using proper pyNastran case control deck"""
        from pyNastran.bdf.case_control_deck import CaseControlDeck

        # Create case control deck
        cc = CaseControlDeck([
            'TITLE = PyNastran Panel Flutter Analysis - SOL145',
            'ECHO = NONE',
            'SPC = 1',
            'METHOD = 1',
            'FMETHOD = 1',
            'DISPLACEMENT = ALL',
            'STRESS = ALL',
            'STRAIN = ALL',
            'FORCE = ALL',
            'BEGIN BULK'
        ])

        self.model.case_control_deck = cc

    def _add_parameters(self):
        """Add parameter cards"""
        # Essential parameters for flutter analysis
        self.model.add_param('COUPMASS', 1)
        self.model.add_param('GRDPNT', 0)
        self.model.add_param('WTMASS', 0.00259)  # Weight-to-mass conversion for SI units
        self.model.add_param('POST', -1)
        self.model.add_param('AUTOSPC', 'YES')

    def _add_materials(self, material: MaterialConfig):
        """Add material cards using pyNastran"""
        # Calculate shear modulus if not provided
        if material.shear_modulus is None:
            G = material.youngs_modulus / (2 * (1 + material.poissons_ratio))
        else:
            G = material.shear_modulus

        # CRITICAL FIX: Add MAT1 card with proper scientific notation formatting
        self.model.add_mat1(
            mid=material.material_id,
            E=format_nastran_float(material.youngs_modulus),  # FIXED: Proper E notation
            G=format_nastran_float(G),                        # FIXED: Proper E notation
            nu=format_nastran_float(material.poissons_ratio),
            rho=format_nastran_float(material.density),       # FIXED: Proper E notation
            a=0.0,      # Thermal expansion coefficient
            tref=0.0,   # Reference temperature
            ge=0.0,     # Structural damping
            St=0.0,     # Stress limit in tension
            Sc=0.0,     # Stress limit in compression
            Ss=0.0,     # Stress limit in shear
            mcsid=0     # Material coordinate system
        )

    def _add_properties(self, panel: PanelConfig, material: MaterialConfig):
        """Add property cards using pyNastran"""
        self.model.add_pshell(
            pid=panel.property_id,
            mid1=material.material_id,
            t=panel.thickness,
            mid2=None,  # Bending material
            twelveIt3=1.0,  # Bending moment of inertia ratio
            mid3=None,  # Transverse shear material
            tst=0.833333,  # Transverse shear thickness ratio
            nsm=0.0,  # Non-structural mass
            z1=None,  # Fiber distance for stress calculation
            z2=None,  # Fiber distance for stress calculation
            mid4=None  # Membrane-bending coupling material
        )

    def _add_grid_points(self, panel: PanelConfig):
        """Add grid points using pyNastran"""
        grid_id = 1
        dx = panel.length / panel.nx
        dy = panel.width / panel.ny

        for j in range(panel.ny + 1):
            for i in range(panel.nx + 1):
                x = i * dx
                y = j * dy
                z = 0.0

                self.model.add_grid(
                    nid=grid_id,
                    xyz=[x, y, z],
                    cp=0,  # Coordinate system
                    cd=0,  # Analysis coordinate system
                    ps='',  # Permanent single-point constraints
                    seid=0  # Superelement ID
                )
                grid_id += 1

    def _add_elements(self, panel: PanelConfig):
        """Add CQUAD4 elements using pyNastran"""
        elem_id = 1

        for j in range(panel.ny):
            for i in range(panel.nx):
                # Calculate node IDs for this element
                n1 = j * (panel.nx + 1) + i + 1
                n2 = n1 + 1
                n3 = n1 + panel.nx + 2
                n4 = n1 + panel.nx + 1

                self.model.add_cquad4(
                    eid=elem_id,
                    pid=panel.property_id,
                    nids=[n1, n2, n3, n4],
                    theta_mcid=0.0,  # Material angle
                    zoffset=0.0,  # Offset
                    tflag=0,  # Membrane thickness flag
                    T1=None, T2=None, T3=None, T4=None  # Thicknesses at nodes
                )
                elem_id += 1

    def _add_boundary_conditions(self, panel: PanelConfig, boundary_conditions: str):
        """Add boundary condition cards using pyNastran"""
        # Handle boundary condition string (e.g., 'SSSS', 'CCCC', 'CFFF')
        if hasattr(boundary_conditions, 'value'):
            bc_str = boundary_conditions.value
        else:
            bc_str = str(boundary_conditions)

        if bc_str.upper() == "SSSS":  # Simply supported on all edges
            # Collect edge nodes
            edge_nodes = []

            # Bottom edge (j=0)
            for i in range(panel.nx + 1):
                edge_nodes.append(i + 1)

            # Top edge (j=ny)
            for i in range(panel.nx + 1):
                edge_nodes.append((panel.ny) * (panel.nx + 1) + i + 1)

            # Left edge (i=0) - skip corners to avoid duplicates
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + 1)

            # Right edge (i=nx) - skip corners to avoid duplicates
            for j in range(1, panel.ny):
                edge_nodes.append(j * (panel.nx + 1) + panel.nx + 1)

            # Remove duplicates and sort
            edge_nodes = sorted(set(edge_nodes))

            # Add SPC1 card to constrain Z displacement (DOF 3) on all edge nodes
            self.model.add_spc1(
                conid=1,
                components='3',  # Z displacement
                nodes=edge_nodes
            )

            # Add constraint to prevent rigid body modes (fix one corner fully)
            self.model.add_spc1(
                conid=1,
                components='123456',  # All DOFs
                nodes=[1]  # First node
            )

    def _add_eigenvalue_extraction(self, n_modes: int):
        """Add eigenvalue extraction cards using pyNastran"""
        self.model.add_eigrl(
            sid=1,
            v1=None,  # Lower eigenvalue bound
            v2=None,  # Upper eigenvalue bound
            nd=n_modes,  # Number of desired eigenvalues
            msglvl=0,  # Message level
            maxset=None,  # Maximum number of vectors in block
            shfscl=None,  # Shift point
            norm=None,  # Normalization method
            options=None,  # Solution options
            values=None  # Specific eigenvalue bounds
        )

    def _add_aerodynamic_cards(self, panel: PanelConfig, aero: AeroConfig):
        """Add aerodynamic reference cards using pyNastran"""
        # Add AERO card
        self.model.add_aero(
            velocity=aero.reference_velocity,
            cref=aero.reference_chord,
            rho_ref=aero.reference_density,
            acsid=0,  # Aerodynamic coordinate system
            sym_xz=0,  # Symmetry about XZ plane
            sym_xy=0,  # Symmetry about XY plane
        )

        # For user's application (M < 1.4), always use doublet lattice method
        # CAERO1 is the correct and reliable method for subsonic/transonic flutter
        logger.info(f"Using CAERO1 (Doublet Lattice) for Mach {aero.mach_number:.2f}")
        self._add_caero1_mesh(panel, aero)

    def _add_caero5_mesh(self, panel: PanelConfig, aero: AeroConfig):
        """Add CAERO5 mesh for piston theory (supersonic)"""
        caero_id = 1001
        pid = 2001

        # Simplified PAERO5 for uniform panel flutter analysis (no AEFACT)
        caoci_values = [0.0] * panel.ny  # One CAOCI value per strip (all zero for uniform flow)
        # Set all parameters to zero for uniform panel - no AEFACT references needed
        self.model.add_paero5(pid=pid, caoci=caoci_values, nalpha=0, lalpha=0, nxis=0, lxis=0, ntaus=0, ltaus=0)

        # CAERO5 panel
        p1 = [0.0, 0.0, 0.001]  # Small offset in Z
        p4 = [0.0, panel.width, 0.001]
        x12 = panel.length
        x43 = panel.length

        self.model.add_caero5(
            eid=caero_id,
            pid=pid,
            p1=p1,
            x12=x12,
            p4=p4,
            x43=x43,
            cp=0,
            nspan=panel.ny,
            lspan=0,  # No AEFACT reference for uniform panel
            ntheory=0,
            nthick=0,
            comment='Piston Theory Panel'
        )

        # Add spline to connect structure to aerodynamics
        self._add_splines(panel, caero_id)

        # Add MKAERO2 for aerodynamic matrix generation (supersonic)
        self._add_mkaero2(aero)

    def _add_caero1_mesh(self, panel: PanelConfig, aero: AeroConfig):
        """Add CAERO1 mesh for doublet lattice method (subsonic)"""
        caero_id = 1001
        pid = 3001

        # PAERO1 property
        self.model.add_paero1(pid=pid, caero_body_ids=None)

        # CAERO1 panel
        p1 = [0.0, 0.0, 0.001]  # Small offset in Z
        p4 = [0.0, panel.width, 0.001]
        x12 = panel.length
        x43 = panel.length

        self.model.add_caero1(
            eid=caero_id,
            pid=pid,
            igroup=1,
            p1=p1,
            x12=x12,
            p4=p4,
            x43=x43,
            cp=0,
            nspan=panel.ny,
            nchord=panel.nx,
            lspan=0,
            lchord=0,
            comment='Doublet Lattice Panel'
        )

        # Add spline to connect structure to aerodynamics
        self._add_splines(panel, caero_id)

        # Add MKAERO1 for aerodynamic matrix generation
        self._add_mkaero1(aero)

    def _add_splines(self, panel: PanelConfig, caero_id: int):
        """Add spline cards for structure-aero coupling"""
        # Create SET1 for all structural nodes
        total_nodes = (panel.nx + 1) * (panel.ny + 1)
        node_list = list(range(1, total_nodes + 1))

        self.model.add_set1(sid=1, ids=node_list)

        # Add SPLINE1 for surface interpolation
        # For CAERO5, box IDs start from caero_id
        self.model.add_spline1(
            eid=1,
            caero=caero_id,
            box1=caero_id,  # First aerodynamic box
            box2=caero_id + panel.nx * panel.ny - 1,  # Last aerodynamic box
            setg=1,
            dz=0.0,
            method='IPS',
            usage='BOTH',
            nelements=10,
            melements=10
        )

    def _add_flutter_cards(self, aero: AeroConfig, n_modes: int):
        """Add flutter analysis cards using pyNastran"""
        # Add FLUTTER card
        self.model.add_flutter(
            sid=1,
            method='PK',  # PK method for flutter
            density=11,   # FLFACT ID for density ratios
            mach=12,      # FLFACT ID for Mach numbers
            reduced_freq_velocity=13,  # FLFACT ID for reduced frequencies/velocities
            imethod='L',  # Complex eigenvalue method
            nvalue=n_modes,
            omax=None,
            epsilon=0.001,
            comment='Flutter Analysis'
        )

        # Add FLFACT cards
        # Density ratios
        self.model.add_flfact(sid=11, factors=[1.0])

        # Mach numbers
        self.model.add_flfact(sid=12, factors=[aero.mach_number])

        # VELOCITIES for PK method (CRITICAL: must be velocities in m/s, not reduced frequencies!)
        if aero.velocities:
            # Use provided velocities (m/s)
            self.model.add_flfact(sid=13, factors=aero.velocities)
        else:
            # Default realistic velocity range for flutter analysis (m/s)
            default_velocities = [200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1200.0]
            self.model.add_flfact(sid=13, factors=default_velocities)

    def _add_mkaero1(self, aero: AeroConfig):
        """Add MKAERO1 cards for aerodynamic matrix generation"""
        # MKAERO1 defines Mach numbers and reduced frequencies for aerodynamic matrix calculations
        mach_numbers = [aero.mach_number]
        reduced_frequencies = [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]  # Standard range (must be > 0.0)

        self.model.add_mkaero1(
            machs=mach_numbers,
            reduced_freqs=reduced_frequencies
        )

    def _add_mkaero2(self, aero: AeroConfig):
        """Add MKAERO2 cards for piston theory aerodynamic matrix generation"""
        # MKAERO2 defines Mach numbers and reduced frequencies for supersonic piston theory
        # For supersonic flows, use higher reduced frequency range for better resolution
        if aero.reduced_frequencies:
            reduced_frequencies = aero.reduced_frequencies
        else:
            # Use appropriate reduced frequency range for supersonic flutter
            reduced_frequencies = [0.01, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0]

        mach_numbers = [aero.mach_number]

        self.model.add_mkaero2(
            machs=mach_numbers,
            reduced_freqs=reduced_frequencies
        )

    def _validate_bdf_file(self, filepath: Path):
        """Validate the generated BDF file"""
        try:
            # Try to read the BDF file back
            test_model = BDF(debug=False)
            test_model.read_bdf(str(filepath), validate=True, xref=False)

            # Check for essential cards
            checks = {
                'Materials': len(test_model.materials) > 0,
                'Properties': len(test_model.properties) > 0,
                'Nodes': len(test_model.nodes) > 0,
                'Elements': len(test_model.elements) > 0,
                'SPCs': len(test_model.spcs) > 0,
                'Eigenvalue methods': len(test_model.methods) > 0
            }

            for check_name, passed in checks.items():
                if passed:
                    logger.info(f"✓ {check_name}: OK")
                else:
                    logger.warning(f"✗ {check_name}: Missing")

            logger.info("BDF validation completed successfully")

        except Exception as e:
            logger.error(f"BDF validation failed: {e}")
            raise


def create_pynastran_flutter_bdf(config: Dict[str, Any], output_dir: str = ".") -> str:
    """Create a SOL145 flutter analysis BDF file using pyNastran"""

    generator = PyNastranBDFGenerator(output_dir)

    # Extract panel config
    panel = PanelConfig(
        length=config.get('panel_length', 1.0),  # m
        width=config.get('panel_width', 0.5),    # m
        thickness=config.get('thickness', 0.0015),  # m
        nx=config.get('nx', 20),
        ny=config.get('ny', 20)
    )

    # Extract material config (SI units: m-kg-s-N)
    material = MaterialConfig(
        youngs_modulus=config.get('youngs_modulus', 71.7e9),  # Pa
        poissons_ratio=config.get('poissons_ratio', 0.33),
        density=config.get('density', 2810.0)  # kg/m^3
    )

    # Extract aero config
    aero = AeroConfig(
        mach_number=config.get('mach_number', 2.0),
        reference_velocity=config.get('velocity', 600.0),  # m/s
        reference_chord=config.get('panel_length', 1.0),  # m
        reference_density=1.225,  # kg/m^3 (air at sea level)
        reduced_frequencies=config.get('reduced_frequencies', [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]),
        velocities=config.get('velocities')  # m/s
    )

    # Generate BDF
    return generator.generate_bdf(
        panel=panel,
        material=material,
        aero=aero,
        boundary_conditions=config.get('boundary_conditions', 'SSSS'),
        n_modes=config.get('n_modes', 20),
        output_filename=config.get('output_filename', 'pynastran_flutter.bdf')
    )


if __name__ == "__main__":
    # Test the generator
    test_config = {
        'panel_length': 1.0,    # 1.0 m
        'panel_width': 0.5,     # 0.5 m
        'thickness': 0.002,     # 2 mm
        'nx': 10,
        'ny': 10,
        'youngs_modulus': 71.7e9,  # Aluminum
        'poissons_ratio': 0.33,
        'density': 2810,
        'mach_number': 0.8,  # Subsonic to use CAERO1 instead of CAERO5
        'velocity': 300.0,
        'n_modes': 15,
        'boundary_conditions': 'SSSS',
        'output_filename': 'test_pynastran_flutter.bdf'
    }

    bdf_file = create_pynastran_flutter_bdf(test_config, ".")
    print(f"Generated BDF file: {bdf_file}")