"""
Simple BDF Generator for NASTRAN SOL145 Flutter Analysis
==========================================================
Uses Sol145BDFGenerator with rotational constraint fixes.
Supports sandwich panels with automatic equivalent property extraction.
"""

from pathlib import Path
from typing import List, Optional, Union, Any
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
        aerodynamic_theory: Optional[str] = None,
        material_object: Optional[Any] = None
    ) -> str:
        """
        Generate NASTRAN BDF file for flutter analysis.

        Args:
            length: Panel length (m)
            width: Panel width (m)
            thickness: Panel thickness (m) - ignored if material_object is SandwichPanel
            nx: Number of elements in x direction
            ny: Number of elements in y direction
            youngs_modulus: Young's modulus (Pa) - ignored if material_object is SandwichPanel
            poissons_ratio: Poisson's ratio - ignored if material_object is SandwichPanel
            density: Material density (kg/m³) - ignored if material_object is SandwichPanel
            mach_number: Mach number
            velocities: List of velocities for flutter analysis (m/s)
            output_file: Output filename
            boundary_conditions: Boundary condition type (default "SSSS")
            n_modes: Number of modes for analysis (default 20)
            aerodynamic_theory: Aerodynamic theory ('PISTON_THEORY' or 'DOUBLET_LATTICE', None=auto)
            material_object: Optional material object (e.g., SandwichPanel) - overrides individual properties

        Returns:
            Path to generated BDF file
        """

        # Check material type and handle accordingly
        is_sandwich = False
        is_composite = False
        if material_object is not None:
            material_type = type(material_object).__name__

            if material_type == 'SandwichPanel':
                is_sandwich = True
                logger.info(f"Detected SandwichPanel: {material_object.name}")
                logger.info(f"  Face: {material_object.face_thickness}mm {material_object.face_material.name}")
                logger.info(f"  Core: {material_object.core_thickness}mm {material_object.core_material.name}")

                # Get equivalent properties
                equiv_props = material_object.get_equivalent_properties()

                # Override material properties with equivalent values
                thickness = material_object.total_thickness / 1000  # mm -> m
                youngs_modulus = equiv_props['effective_youngs_modulus']  # Pa
                poissons_ratio = material_object.face_material.poissons_ratio  # Use face material's Poisson ratio
                density = material_object.total_density  # kg/m³

                logger.info(f"Sandwich equivalent properties:")
                logger.info(f"  Total thickness: {thickness*1000:.3f} mm")
                logger.info(f"  Effective E: {youngs_modulus/1e9:.2f} GPa")
                logger.info(f"  Effective density: {density:.1f} kg/m³")
                logger.info(f"  Weight saving: {equiv_props['weight_saving']:.1f}%")
                logger.info(f"  Flexural rigidity: {equiv_props['flexural_rigidity']:.3e} N·m")

            elif material_type == 'CompositeLaminate':
                is_composite = True
                logger.info(f"Detected CompositeLaminate: {material_object.name}")
                logger.info(f"  Number of plies: {len(material_object.laminas)}")
                logger.info(f"  Total thickness: {material_object.total_thickness} mm")

                # For composite, thickness comes from laminate
                thickness = material_object.total_thickness / 1000  # mm -> m

                # Calculate effective density (weighted average)
                total_mass = 0
                for lamina in material_object.laminas:
                    lamina_mass = lamina.material.density * lamina.thickness
                    total_mass += lamina_mass
                density = total_mass / material_object.total_thickness  # kg/m³

                logger.info(f"Composite properties:")
                logger.info(f"  Total thickness: {thickness*1000:.3f} mm")
                logger.info(f"  Effective density: {density:.1f} kg/m³")

                # Note: E and nu not used for composite - will write PCOMP/MAT8 cards instead
                # Set dummy values to avoid errors in downstream code
                youngs_modulus = 100e9  # Dummy value
                poissons_ratio = 0.3     # Dummy value

        # CRITICAL DEBUG v2.11.0: Check density value before conversion
        print("\n" + "="*80)
        print(">>> v2.11.0 DENSITY DEBUG - SimpleBDFGenerator.generate_flutter_bdf() <<<")
        print(f"Input density (kg/m³): {density}")
        print(f"Expected for aluminum: 2810 kg/m³")
        print(f"After conversion (tonne/mm³): {density * 1e-12:.2E}")
        print(f"Expected after conversion: 2.81E-09 tonne/mm³ (NASTRAN uses mm-tonne-s-N!)")
        print("="*80 + "\n")

        # CRITICAL DEBUG v2.5.0: Check Mach number
        print("\n" + "="*80)
        print(">>> v2.5.0 MACH NUMBER DEBUG - SimpleBDFGenerator.generate_flutter_bdf() <<<")
        print(f"Input Mach number: {mach_number}")
        print(f"Aerodynamic theory: {aerodynamic_theory if aerodynamic_theory else 'AUTO'}")
        print("="*80 + "\n")

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
            density=density * 1e-12,  # kg/m³ → tonne/mm³ (NASTRAN uses mm-tonne-s-N, not mm-kg-s-N!)
            material_id=1
        )

        # Calculate reference values for aerodynamics
        reference_velocity = velocities[len(velocities)//2] if velocities else 1000.0  # m/s
        reference_chord = length * 1000  # m → mm

        # Standard atmosphere at sea level
        reference_density = 1.225 * 1e-12  # kg/m³ → tonne/mm³ (NASTRAN mm-tonne-s-N system)

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
                aerodynamic_theory=aerodynamic_theory,
                material_object=material_object if is_composite else None  # Pass composite material object
            )

            logger.info(f"BDF file generated successfully: {bdf_path}")
            return str(bdf_path)

        except Exception as e:
            logger.error(f"Failed to generate BDF: {e}")
            raise
