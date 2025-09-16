"""
Real Analysis Executor
=====================

This module integrates the validated NASTRAN-aeroelasticity analysis backend
with the modern customtkinter GUI, providing real flutter analysis capabilities.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Callable
import logging
import numpy as np
import threading
import time
import tempfile
import datetime

from .nastran_runner import NastranRunner

# Add nastran-aeroelasticity source to path
current_dir = Path(__file__).parent.parent
nastran_aero_path = current_dir / "nastran-aeroelasticity" / "src"
if nastran_aero_path.exists():
    sys.path.insert(0, str(nastran_aero_path))

class AnalysisExecutor:
    """Executes real flutter analysis using validated backend"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_analysis_modules()

    def _load_analysis_modules(self):
        """Load the analysis modules from nastran-aeroelasticity"""
        self.modules_loaded = False

        try:
            # Import core nastran modules
            from nastran.structures.material import IsotropicMaterial, OrthotropicMaterial
            from nastran.structures.panel import IsotropicPlate
            from nastran.aero.analysis.panel_flutter import PanelFlutterPistonAnalysisModel, PanelFlutterSubcase
            from nastran.aero.superpanels import SuperAeroPanel5, SuperAeroPanel1
            from nastran.structures.bc import create_spcs_and_subcases, generate_bc_case

            # Store the imported classes
            self.IsotropicMaterial = IsotropicMaterial
            self.OrthotropicMaterial = OrthotropicMaterial
            self.IsotropicPlate = IsotropicPlate
            self.PanelFlutterPistonAnalysisModel = PanelFlutterPistonAnalysisModel
            self.PanelFlutterSubcase = PanelFlutterSubcase
            self.SuperAeroPanel5 = SuperAeroPanel5
            self.SuperAeroPanel1 = SuperAeroPanel1
            self.create_spcs_and_subcases = create_spcs_and_subcases
            self.generate_bc_case = generate_bc_case

            # OrthotropicPlate is optional
            try:
                from nastran.structures.panel import OrthotropicPlate
                self.OrthotropicPlate = OrthotropicPlate
            except ImportError:
                self.logger.info("OrthotropicPlate not available (optional)")

            # Try to import post-processing modules
            try:
                from nastran.post.f06 import read_f06
                from nastran.post.flutter import get_critical_roots, join_flutter_pages, flutter_pages_to_df
                from nastran.post.plots import plot_vf_vg

                self.read_f06 = read_f06
                self.get_critical_roots = get_critical_roots
                self.join_flutter_pages = join_flutter_pages
                self.flutter_pages_to_df = flutter_pages_to_df
                self.plot_vf_vg = plot_vf_vg
                self.post_processing_available = True
            except ImportError as e:
                self.logger.warning(f"Post-processing modules not available: {e}")
                self.post_processing_available = False

            # Fix pyNastran compatibility if needed
            self._fix_pyNastran_compatibility()

            self.modules_loaded = True
            self.logger.info("✓ Analysis modules loaded successfully from nastran-aeroelasticity")

        except ImportError as e:
            self.modules_loaded = False
            self.logger.error(f"Failed to load analysis modules: {e}")

    def _fix_pyNastran_compatibility(self):
        """Fix pyNastran compatibility issues"""
        from pyNastran.bdf.bdf import BDF

        if not hasattr(BDF, '_add_structural_material_object'):
            def _add_structural_material_object(self, mat):
                """Compatibility patch for nastran-aeroelasticity"""
                if hasattr(mat, 'mid'):
                    self.materials[mat.mid] = mat
                return mat

            BDF._add_structural_material_object = _add_structural_material_object

        # Fix add_spline2 method signature compatibility
        try:
            # Patch the BDF add_spline2 method directly
            original_add_spline2 = BDF.add_spline2

            def patched_add_spline2(self, eid, caero, box1=None, box2=None, setg=None,
                                  dz=0.0, dtor=1.0, cid=0, dthx=0.0, dthy=0.0,
                                  usage='BOTH', comment='', **kwargs):
                """Compatibility patch for add_spline2 method"""
                # Handle old-style parameters that may come from nastran-aeroelasticity
                if 'id1' in kwargs:
                    box1 = kwargs.pop('id1')
                if 'id2' in kwargs:
                    box2 = kwargs.pop('id2')

                # Set defaults if not provided
                if box1 is None:
                    box1 = 1
                if box2 is None:
                    box2 = 100

                # Filter out any remaining incompatible kwargs
                filtered_kwargs = {k: v for k, v in kwargs.items()
                                 if k not in ['nelements', 'melements', 'method']}

                return original_add_spline2(
                    self, eid, caero, box1, box2, setg,
                    dz=dz, dtor=dtor, cid=cid, dthx=dthx, dthy=dthy,
                    usage=usage, comment=comment, **filtered_kwargs
                )

            BDF.add_spline2 = patched_add_spline2
            self.logger.info("Applied pyNastran add_spline2 compatibility patch")

        except Exception as e:
            self.logger.warning(f"Could not patch add_spline2 method: {e}")

    def run_flutter_analysis(self,
                           structural_model: Any,
                           aerodynamic_model: Any,
                           analysis_config: Dict[str, Any],
                           progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Run complete flutter analysis using the nastran-aeroelasticity backend

        Args:
            structural_model: Structural model from GUI
            aerodynamic_model: Aerodynamic model from GUI
            analysis_config: Analysis configuration
            progress_callback: Function to call for progress updates

        Returns:
            Dictionary containing analysis results
        """
        if not self.modules_loaded:
            return {"success": False, "error": "Analysis modules not available"}

        try:
            if progress_callback:
                progress_callback("Initializing analysis...", 0.1)

            # Update NASTRAN executable if provided
            nastran_executable = analysis_config.get('nastran_executable')
            if nastran_executable and nastran_executable != 'nastran':
                self.logger.info(f"Using custom NASTRAN executable: {nastran_executable}")
                # You can store this for use in the analysis backend
                # For now, just log it as the backend needs to be updated to use it

            # Use the actual nastran-aeroelasticity workflow
            result = self._run_nastran_aeroelasticity_analysis(
                structural_model,
                aerodynamic_model,
                analysis_config,
                progress_callback
            )

            if progress_callback:
                progress_callback("Analysis complete!", 1.0)

            return result

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def _run_nastran_aeroelasticity_analysis(self, structural_model, aerodynamic_model, config, progress_callback):
        """Run analysis using the actual nastran-aeroelasticity workflow"""
        try:
            if progress_callback:
                progress_callback("Setting up panel geometry...", 0.2)

            # Extract parameters from GUI models
            geometry = structural_model.geometry
            flow = aerodynamic_model.flow_conditions

            if not geometry or not flow:
                return {"success": False, "error": "Incomplete model definition - missing geometry or flow conditions"}

            # Create analysis using nastran-aeroelasticity approach with default Aluminum properties
            if progress_callback:
                progress_callback("Creating material model...", 0.3)

            # Try to get material from structural model, or use default Aluminum 6061-T6
            gui_material = None
            if hasattr(structural_model, 'get_material'):
                gui_material = structural_model.get_material()

            if gui_material and hasattr(gui_material, 'youngs_modulus'):
                # Use material from GUI
                nastran_material = self.IsotropicMaterial(
                    1,                                           # Material ID
                    gui_material.youngs_modulus / 1e6,         # Convert Pa to MPa
                    gui_material.poissons_ratio,               # Poisson's ratio
                    gui_material.shear_modulus / 1e6,          # Convert Pa to MPa
                    gui_material.density * 1e-9,               # Convert kg/m³ to ton/mm³
                    alpha=getattr(gui_material, 'thermal_expansion', 21e-6)
                )
                self.logger.info(f"Using GUI material: E={gui_material.youngs_modulus/1e9:.1f} GPa")
            else:
                # Use default Aluminum 6061-T6 properties (matching Metallic notebook)
                # Values from Metallic.ipynb: E=71.7 GPa, nu=0.33, rho=2.81 g/cm³
                nastran_material = self.IsotropicMaterial(
                    1,                    # Material ID
                    71700.,              # Young's modulus in MPa (71.7 GPa)
                    0.33,                # Poisson's ratio
                    26900.,              # Shear modulus in MPa (26.9 GPa)
                    2.81e-9,             # Density in ton/mm³ (2.81 g/cm³)
                    alpha=21e-6          # Thermal expansion coefficient
                )
                self.logger.info("Using default Aluminum 6061-T6 properties")

            if progress_callback:
                progress_callback("Creating panel geometry...", 0.4)

            # Convert geometry to mm (nastran-aeroelasticity uses mm)
            a = geometry.length * 1000    # m to mm
            b = geometry.width * 1000     # m to mm
            thickness = geometry.thickness * 1000  # m to mm

            # Define corner points
            import numpy as np
            p1 = np.array([0, 0, 0])
            p2 = p1 + np.array([a, 0, 0])
            p3 = p1 + np.array([a, b, 0])
            p4 = p1 + np.array([0, b, 0])

            # Mesh parameters
            nchord = structural_model.mesh_params.nx if hasattr(structural_model, 'mesh_params') else 10
            nspan = structural_model.mesh_params.ny if hasattr(structural_model, 'mesh_params') else 10

            if progress_callback:
                progress_callback("Generating structural model...", 0.5)

            # Create isotropic plate
            plate = self.IsotropicPlate.create_plate(
                p1, p2, p3, p4, nspan, nchord, 1, thickness, nastran_material
            )

            if progress_callback:
                progress_callback("Setting up flutter analysis...", 0.6)

            # Configure flutter analysis
            flutter_config = {
                'vref': 1000.,                        # Reference velocity (mm/s)
                'ref_rho': 1.225e-12,                 # Air density reference (ton/mm^3)
                'ref_chord': a,                       # Reference chord (mm)
                'n_modes': config.get('n_modes', 15), # Number of modes
                'frequency_limits': [0.0, 1000.],     # Frequency range (Hz)
                'method': 'PK',                       # Flutter method
                'densities_ratio': [0.5],             # rho/rho_ref
                'machs': [flow.mach_number],          # Mach numbers
                'alphas': [0., 0., 0., 0.],           # Angles of attack
                'reduced_frequencies': [0.001, 0.1, 0.2, 0.4],  # k values
                'velocities': np.linspace(
                    config.get('velocity_min', 800),
                    config.get('velocity_max', 1200),
                    config.get('velocity_points', 20)
                ) * 1000,  # Convert m/s to mm/s
            }

            params = {
                'VREF': 1000.0,
                'COUPMASS': 1,
                'LMODES': flutter_config['n_modes'],
                'WTMASS': 1.,
                'GRDPNT': 1,
                'OPPHIPA': 1,
            }

            if progress_callback:
                progress_callback("Creating flutter analysis model...", 0.7)

            # Create analysis model
            analysis = self.PanelFlutterPistonAnalysisModel(plate.bdf, params=params)
            analysis.set_global_case_from_dict(flutter_config)

            if progress_callback:
                progress_callback("Applying boundary conditions...", 0.8)

            # Apply boundary conditions
            bc_type = str(structural_model.boundary_condition).split('.')[-1] if hasattr(structural_model.boundary_condition, 'value') else 'SSSS'
            spc_cases = {1: self.generate_bc_case(bc_type)}

            nodes = plate.limit_nodes()
            nodes[2] = nodes[2][1:-1] if len(nodes[2]) > 2 else nodes[2]
            nodes[3] = nodes[3][1:-1] if len(nodes[3]) > 2 else nodes[3]

            self.create_spcs_and_subcases(analysis, spc_cases, nodes, self.PanelFlutterSubcase)

            if progress_callback:
                progress_callback("Adding aerodynamic model...", 0.9)

            # Add piston theory aerodynamics
            spanel_p = self.SuperAeroPanel5(1, p1, p2, p3, p4, nchord, nspan, theory='VANDYKE')
            analysis.add_superpanel(spanel_p)

            if progress_callback:
                progress_callback("Writing flutter analysis cards...", 0.92)

            # Generate all flutter analysis cards (FLUTTER, FLFACT, EIGRL, AERO, etc.)
            analysis.write_cards()
            self.logger.info("Flutter analysis cards written to BDF model")

            # Create working directory with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            working_dir = Path.cwd() / "analysis_temp" / f"flutter_analysis_{timestamp}"
            working_dir.mkdir(parents=True, exist_ok=True)

            # Generate BDF file
            bdf_filename = f"flutter_analysis_{timestamp}.bdf"
            bdf_path = working_dir / bdf_filename

            if progress_callback:
                progress_callback("Writing complete BDF file...", 0.95)

            # Write complete BDF file with flutter analysis
            analysis.model.write_bdf(str(bdf_path), enddata=True)
            self.logger.info(f"BDF file written: {bdf_path}")

            # Get NASTRAN executable path from config
            nastran_executable = config.get('nastran_executable', 'nastran')

            if progress_callback:
                progress_callback("Executing NASTRAN...", 0.96)

            # Check if we're in test mode (no NASTRAN execution)
            test_mode = config.get('test_mode', False) or nastran_executable == 'test'

            if test_mode:
                self.logger.info("Running in test mode - BDF generated but NASTRAN not executed")

                if progress_callback:
                    progress_callback("Test mode: BDF generated successfully", 1.0)

                return {
                    "success": True,
                    "method": "NASTRAN Aeroelasticity (Test Mode)",
                    "analysis_ready": True,
                    "configuration": {
                        "panel_dimensions": f"{a:.1f}x{b:.1f}x{thickness:.1f}mm",
                        "material": "Aluminum 6061-T6",
                        "boundary_conditions": bc_type,
                        "mach_number": flow.mach_number,
                        "velocity_range": f"{config.get('velocity_min', 800)}-{config.get('velocity_max', 1200)} m/s",
                        "mesh": f"{nchord}x{nspan}"
                    },
                    "note": f"BDF file generated successfully. NASTRAN execution required for flutter results.",
                    "critical_flutter_speed": None,
                    "critical_flutter_frequency": None,
                    "bdf_generated": True,
                    "bdf_file": str(bdf_path),
                    "working_directory": str(working_dir),
                    "test_mode": True
                }

            # Execute NASTRAN analysis
            runner = NastranRunner(nastran_executable)

            # Validate NASTRAN executable first
            if not runner.validate_nastran_executable():
                self.logger.warning(f"NASTRAN executable validation failed: {nastran_executable}")
                self.logger.info("Continuing with execution anyway - validation may fail for working executables")

            nastran_result = runner.run_analysis(
                str(bdf_path),
                str(working_dir),
                timeout=3600,  # 1 hour timeout
                progress_callback=lambda msg, prog: progress_callback(f"NASTRAN: {msg}", 0.96 + prog * 0.03) if progress_callback else None
            )

            if not nastran_result["success"]:
                return {
                    "success": False,
                    "error": f"NASTRAN execution failed: {nastran_result.get('error', 'Unknown error')}",
                    "working_directory": str(working_dir),
                    "bdf_file": str(bdf_path),
                    "nastran_executable": nastran_executable
                }

            if progress_callback:
                progress_callback("Parsing F06 results...", 0.99)

            # Parse F06 results for flutter data
            flutter_results = self._parse_flutter_f06(nastran_result["f06_file"])

            if progress_callback:
                progress_callback("Analysis complete!", 1.0)

            # Return real analysis results
            return {
                "success": True,
                "method": "NASTRAN Aeroelasticity",
                "analysis_ready": True,
                "configuration": {
                    "panel_dimensions": f"{a:.1f}x{b:.1f}x{thickness:.1f}mm",
                    "material": "Aluminum 6061-T6",
                    "boundary_conditions": bc_type,
                    "mach_number": flow.mach_number,
                    "velocity_range": f"{config.get('velocity_min', 800)}-{config.get('velocity_max', 1200)} m/s",
                    "mesh": f"{nchord}x{nspan}"
                },
                "note": f"NASTRAN analysis completed in {nastran_result['execution_time']:.1f} seconds",
                "critical_flutter_speed": flutter_results.get("critical_velocity", None),
                "critical_flutter_frequency": flutter_results.get("critical_frequency", None),
                "bdf_generated": True,
                "bdf_file": str(bdf_path),
                "f06_file": nastran_result["f06_file"],
                "working_directory": str(working_dir),
                "execution_time": nastran_result["execution_time"],
                "flutter_data": flutter_results.get("flutter_data", {}),
                "nastran_stdout_lines": nastran_result.get("stdout_lines", 0),
                "nastran_stderr_lines": nastran_result.get("stderr_lines", 0)
            }

        except Exception as e:
            return {"success": False, "error": f"Nastran-aeroelasticity analysis failed: {str(e)}"}

    def _parse_flutter_f06(self, f06_file_path: str) -> Dict[str, Any]:
        """
        Parse F06 file for flutter results using nastran-aeroelasticity capabilities.

        Args:
            f06_file_path: Path to the F06 file

        Returns:
            Dictionary containing flutter results
        """
        try:
            f06_path = Path(f06_file_path)
            if not f06_path.exists():
                self.logger.error(f"F06 file not found: {f06_file_path}")
                return {"error": "F06 file not found"}

            self.logger.info(f"Parsing F06 file: {f06_path}")

            # Import F06 reading capabilities
            from nastran.post.f06 import read_f06
            from nastran.post.f06.flutter import join_flutter_pages, flutter_pages_to_df, get_critical_roots

            # Read F06 file
            f06_results = read_f06(str(f06_path))
            self.logger.info(f"F06 file read successfully")

            # Check if flutter results exist
            if not hasattr(f06_results, 'flutter') or not f06_results.flutter:
                self.logger.warning("No flutter results found in F06 file")
                return {"error": "No flutter results found in F06 file"}

            # Process flutter pages
            flutter_pages = join_flutter_pages(f06_results.flutter)
            if not flutter_pages:
                self.logger.warning("No flutter pages found")
                return {"error": "No flutter pages found"}

            # Convert to DataFrame
            flutter_df = flutter_pages_to_df(flutter_pages)
            if flutter_df.empty:
                self.logger.warning("Flutter DataFrame is empty")
                return {"error": "Flutter DataFrame is empty"}

            self.logger.info(f"Flutter DataFrame shape: {flutter_df.shape}")
            self.logger.info(f"Flutter DataFrame columns: {list(flutter_df.columns)}")

            # Get critical flutter conditions
            critical_results = get_critical_roots(flutter_df, epsilon=1e-9, var_ref="DAMPING")

            if critical_results.empty:
                self.logger.warning("No critical flutter conditions found")
                return {
                    "error": "No critical flutter conditions found",
                    "flutter_data": flutter_df.to_dict('records') if not flutter_df.empty else {}
                }

            # Extract critical flutter parameters
            # Convert from mm/s to m/s for velocity
            critical_velocity_mm_s = critical_results['VELOCITY'].iloc[0] if 'VELOCITY' in critical_results else None
            critical_velocity_m_s = critical_velocity_mm_s / 1000.0 if critical_velocity_mm_s is not None else None

            critical_frequency = critical_results['FREQUENCY'].iloc[0] if 'FREQUENCY' in critical_results else None

            self.logger.info(f"Critical flutter velocity: {critical_velocity_m_s} m/s")
            self.logger.info(f"Critical flutter frequency: {critical_frequency} Hz")

            return {
                "success": True,
                "critical_velocity": critical_velocity_m_s,
                "critical_frequency": critical_frequency,
                "critical_results": critical_results.to_dict('records')[0] if not critical_results.empty else {},
                "flutter_data": flutter_df.to_dict('records'),
                "num_flutter_points": len(flutter_df),
                "velocity_range": [flutter_df['VELOCITY'].min() / 1000.0, flutter_df['VELOCITY'].max() / 1000.0] if 'VELOCITY' in flutter_df else None,
                "frequency_range": [flutter_df['FREQUENCY'].min(), flutter_df['FREQUENCY'].max()] if 'FREQUENCY' in flutter_df else None
            }

        except ImportError as e:
            self.logger.error(f"F06 parsing modules not available: {e}")
            return {"error": f"F06 parsing modules not available: {e}"}

        except Exception as e:
            self.logger.error(f"F06 parsing failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"F06 parsing failed: {e}"}

    def _convert_structural_model(self, structural_model: Any) -> Any:
        """Convert GUI structural model to analysis format"""
        if not structural_model or not structural_model.geometry:
            raise ValueError("Structural model not defined")

        # Get material properties
        material_props = structural_model.properties[0] if structural_model.properties else None
        if not material_props:
            raise ValueError("Material properties not defined")

        # Use default aluminum properties if not specified
        return self.PanelProperties(
            length=structural_model.geometry.length,
            width=structural_model.geometry.width,
            thickness=structural_model.geometry.thickness,
            youngs_modulus=71.7e9,  # Default aluminum
            poissons_ratio=0.33,
            density=2810,
            boundary_conditions=structural_model.boundary_condition.value if hasattr(structural_model.boundary_condition, 'value') else str(structural_model.boundary_condition)
        )

    def _convert_aerodynamic_model(self, aerodynamic_model: Any) -> Any:
        """Convert GUI aerodynamic model to analysis format"""
        if not aerodynamic_model or not aerodynamic_model.flow_conditions:
            raise ValueError("Aerodynamic model not defined")

        flow = aerodynamic_model.flow_conditions
        return self.FlowConditions(
            mach_number=flow.mach_number,
            altitude=flow.altitude,
            temperature=flow.temperature
        )

    def _run_piston_theory_analysis(self, panel_props: Any, flow_conditions: Any,
                                   config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run piston theory analysis"""
        try:
            solver = self.PistonTheorySolver()

            # Get velocity range from config
            v_min = config.get('velocity_min', 50)
            v_max = config.get('velocity_max', 1000)
            num_points = config.get('velocity_points', 20)

            if progress_callback:
                progress_callback("Running piston theory solver...", 0.5)

            # Run analysis over velocity range
            velocities = np.linspace(v_min, v_max, num_points)
            results = []

            for i, velocity in enumerate(velocities):
                # Create modified flow conditions for this velocity
                flow_at_velocity = self.FlowConditions(
                    mach_number=flow_conditions.mach_number,
                    altitude=flow_conditions.altitude,
                    temperature=flow_conditions.temperature
                )

                # Get flutter result
                result = solver.find_critical_flutter_speed(panel_props, flow_at_velocity)
                results.append({
                    'velocity': velocity,
                    'flutter_speed': result.flutter_speed,
                    'flutter_frequency': result.flutter_frequency,
                    'damping': result.damping,
                    'stable': result.damping < 0
                })

                if progress_callback:
                    progress = 0.5 + 0.4 * (i + 1) / len(velocities)
                    progress_callback(f"Computing point {i+1}/{len(velocities)}", progress)

            # Find critical flutter point
            critical_result = solver.find_critical_flutter_speed(panel_props, flow_conditions)

            return {
                "success": True,
                "method": "Piston Theory",
                "critical_flutter_speed": critical_result.flutter_speed,
                "critical_flutter_frequency": critical_result.flutter_frequency,
                "critical_damping": critical_result.damping,
                "results_points": results,
                "velocities": velocities.tolist(),
                "flutter_speeds": [r['flutter_speed'] for r in results],
                "flutter_frequencies": [r['flutter_frequency'] for r in results],
                "dampings": [r['damping'] for r in results]
            }

        except Exception as e:
            return {"success": False, "error": f"Piston theory analysis failed: {str(e)}"}

    def _run_doublet_lattice_analysis(self, panel_props: Any, flow_conditions: Any,
                                     config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run doublet lattice analysis"""
        try:
            if progress_callback:
                progress_callback("Doublet lattice analysis not yet implemented", 0.8)

            # For now, return simulated results
            # TODO: Implement actual doublet lattice solver integration
            return {
                "success": True,
                "method": "Doublet Lattice (Simulated)",
                "critical_flutter_speed": 850.0,
                "critical_flutter_frequency": 150.0,
                "critical_damping": -0.01,
                "note": "Doublet lattice implementation pending"
            }

        except Exception as e:
            return {"success": False, "error": f"Doublet lattice analysis failed: {str(e)}"}

    def _run_nastran_analysis(self, panel_props: Any, flow_conditions: Any,
                             config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run NASTRAN analysis"""
        try:
            if progress_callback:
                progress_callback("Generating BDF file...", 0.4)

            # Generate BDF file
            generator = self.NastranBDFGenerator()

            panel_config = {
                'length': panel_props.length,
                'width': panel_props.width,
                'thickness': panel_props.thickness,
                'youngs_modulus': panel_props.youngs_modulus,
                'poissons_ratio': panel_props.poissons_ratio,
                'density': panel_props.density
            }

            mesh_config = {
                'nx': config.get('mesh_nx', 10),
                'ny': config.get('mesh_ny', 10)
            }

            flow_config = {
                'mach': flow_conditions.mach_number,
                'dynamic_pressure': config.get('dynamic_pressure', 50000)
            }

            bdf_content = generator.generate_flutter_bdf(
                panel_config, mesh_config, flow_config,
                boundary_conditions=panel_props.boundary_conditions,
                analysis_type='SOL_145'
            )

            if progress_callback:
                progress_callback("BDF generated. NASTRAN execution requires separate setup.", 0.8)

            # Save BDF file
            bdf_path = Path("flutter_analysis.bdf")
            with open(bdf_path, 'w') as f:
                f.write(bdf_content)

            return {
                "success": True,
                "method": "NASTRAN",
                "bdf_file": str(bdf_path),
                "bdf_lines": len(bdf_content.split('\\n')),
                "note": "BDF file generated. Run with NASTRAN solver externally.",
                "critical_flutter_speed": None,
                "critical_flutter_frequency": None
            }

        except Exception as e:
            return {"success": False, "error": f"NASTRAN analysis failed: {str(e)}"}

    def _run_multi_solver_analysis(self, panel_props: Any, flow_conditions: Any,
                                  config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run multi-solver comparison analysis"""
        try:
            analyzer = self.MultiSolverAnalyzer()

            # Define methods to compare
            methods = [self.SolverMethod.PISTON_THEORY]
            if flow_conditions.mach_number < 1.2:
                methods.append(self.SolverMethod.DOUBLET_LATTICE)

            if progress_callback:
                progress_callback(f"Running {len(methods)} solver comparison...", 0.4)

            # Run comparison
            velocity_range = (config.get('velocity_min', 50), config.get('velocity_max', 1000))
            num_points = min(config.get('velocity_points', 20), 10)  # Limit for speed

            results = analyzer.analyze_with_multiple_solvers(
                panel_props, flow_conditions, methods, velocity_range, num_points
            )

            if progress_callback:
                progress_callback("Comparing results...", 0.8)

            # Process comparison results
            comparison = analyzer.compare_results(results)

            return {
                "success": True,
                "method": "Multi-Solver Comparison",
                "results": {
                    method: {
                        "flutter_speed": result.flutter_speed if result else None,
                        "flutter_frequency": result.flutter_frequency if result else None,
                        "damping": result.damping if result else None
                    } for method, result in results.items()
                },
                "comparison": comparison,
                "recommended_result": comparison.recommended_result if hasattr(comparison, 'recommended_result') else None
            }

        except Exception as e:
            return {"success": False, "error": f"Multi-solver analysis failed: {str(e)}"}

    def generate_bdf_file(self, structural_model: Any, aerodynamic_model: Any,
                         output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate NASTRAN BDF file from GUI models"""
        if not self.modules_loaded:
            return {"success": False, "error": "Analysis modules not available"}

        try:
            generator = self.NastranBDFGenerator()

            # Convert models
            panel_props = self._convert_structural_model(structural_model)
            flow_conditions = self._convert_aerodynamic_model(aerodynamic_model)

            # Generate BDF
            panel_config = {
                'length': panel_props.length,
                'width': panel_props.width,
                'thickness': panel_props.thickness,
                'youngs_modulus': panel_props.youngs_modulus,
                'poissons_ratio': panel_props.poissons_ratio,
                'density': panel_props.density
            }

            mesh_config = {
                'nx': structural_model.mesh_params.nx if structural_model.mesh_params else 10,
                'ny': structural_model.mesh_params.ny if structural_model.mesh_params else 10
            }

            flow_config = {
                'mach': flow_conditions.mach_number,
                'dynamic_pressure': aerodynamic_model.flow_conditions.dynamic_pressure
            }

            bdf_content = generator.generate_flutter_bdf(
                panel_config, mesh_config, flow_config,
                boundary_conditions=panel_props.boundary_conditions,
                analysis_type='SOL_145'
            )

            # Save to file
            if output_path is None:
                output_path = Path("panel_flutter_analysis.bdf")

            with open(output_path, 'w') as f:
                f.write(bdf_content)

            return {
                "success": True,
                "bdf_file": str(output_path),
                "bdf_lines": len(bdf_content.split('\\n')),
                "content_preview": '\\n'.join(bdf_content.split('\\n')[:10])
            }

        except Exception as e:
            return {"success": False, "error": f"BDF generation failed: {str(e)}"}

# Global instance
executor = AnalysisExecutor()