"""
Simple BDF Generator for NASTRAN SOL145 Flutter Analysis
==========================================================
Uses Sol145BDFGenerator with rotational constraint fixes.
"""

from pathlib import Path
from typing import List, Optional
import logging

from .bdf_generator_sol145_fixed import (
    Sol145BDFGenerator,
    PanelConfig,
    MaterialConfig,
    AeroConfig
)

logger = logging.getLogger(__name__)


class SimpleBDFGenerator:
    """
    Simple wrapper for PyNastranBDFGenerator with a clean interface.
    Converts simple parameters to PyNastran config objects.
    """

    def __init__(self, output_dir: str = "."):
        """Initialize with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generator = Sol145BDFGenerator(output_dir=str(self.output_dir))
        logger.info(f"SimpleBDFGenerator initialized with Sol145BDFGenerator")

    def generate_flutter_bdf(
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
        output_file: str,
        boundary_conditions: str = "SSSS",
        n_modes: int = 20,
        aerodynamic_theory: Optional[str] = None
    ) -> str:
        """
        Generate NASTRAN BDF file for flutter analysis.

        Args:
            length: Panel length (m)
            width: Panel width (m)
            thickness: Panel thickness (m)
            nx: Number of elements in x direction
            ny: Number of elements in y direction
            youngs_modulus: Young's modulus (Pa)
            poissons_ratio: Poisson's ratio
            density: Material density (kg/m³)
            mach_number: Mach number
            velocities: List of velocities for flutter analysis (m/s)
            output_file: Output filename
            boundary_conditions: Boundary condition type (default "SSSS")
            n_modes: Number of modes for analysis (default 20)
            aerodynamic_theory: Aerodynamic theory ('PISTON_THEORY' or 'DOUBLET_LATTICE', None=auto)

        Returns:
            Path to generated BDF file
        """

        logger.info(f"Generating BDF: {length}m x {width}m x {thickness}m, {nx}x{ny} mesh")
        logger.info(f"Material: E={youngs_modulus/1e9:.1f}GPa, rho={density:.0f}kg/m³")
        logger.info(f"Flow: M={mach_number:.2f}, velocities={len(velocities)} points")
        logger.info(f"Aerodynamic theory: {aerodynamic_theory if aerodynamic_theory else 'AUTO (based on Mach)'}")

        # Convert SI units (m, kg, Pa) to Sol145 units (mm, kg, s, N)
        # Sol145BDFGenerator uses mm-kg-s-N system
        panel = PanelConfig(
            length=length * 1000,  # m → mm
            width=width * 1000,    # m → mm
            thickness=thickness * 1000,  # m → mm
            nx=nx,
            ny=ny,
            material_id=1,
            property_id=1
        )

        material = MaterialConfig(
            youngs_modulus=youngs_modulus / 1e6,  # Pa → MPa (N/mm²)
            poissons_ratio=poissons_ratio,
            density=density * 1e-9,  # kg/m³ → kg/mm³
            material_id=1
        )

        # Calculate reference values for aerodynamics
        reference_velocity = velocities[len(velocities)//2] if velocities else 1000.0  # m/s
        reference_chord = length * 1000  # m → mm

        # Standard atmosphere at sea level
        reference_density = 1.225 * 1e-9  # kg/m³ → kg/mm³

        # Default reduced frequencies for flutter analysis
        reduced_frequencies = [0.001, 0.01, 0.1, 0.2]

        # Convert velocities to mm/s
        velocities_mm = [v * 1000 for v in velocities]  # m/s → mm/s

        aero = AeroConfig(
            mach_number=mach_number,
            reference_velocity=reference_velocity * 1000,  # m/s → mm/s
            reference_chord=reference_chord,  # mm
            reference_density=reference_density,  # kg/mm³
            reduced_frequencies=reduced_frequencies,
            velocities=velocities_mm  # mm/s
        )

        # Generate BDF file
        output_path = self.output_dir / output_file

        try:
            bdf_path = self.generator.generate_bdf(
                panel=panel,
                material=material,
                aero=aero,
                boundary_conditions=boundary_conditions,
                n_modes=n_modes,
                output_filename=output_file,
                aerodynamic_theory=aerodynamic_theory
            )

            logger.info(f"BDF file generated successfully: {bdf_path}")
            return str(bdf_path)

        except Exception as e:
            logger.error(f"Failed to generate BDF: {e}")
            raise
