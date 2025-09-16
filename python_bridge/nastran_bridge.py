#!/usr/bin/env python3
"""
NASTRAN Panel Flutter Analysis Bridge

This module provides a Python bridge between the Flutter GUI and the
nastran-aeroelasticity library for panel flutter analysis.
"""

import sys
import os
import json
import traceback
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the nastran-aeroelasticity source to Python path
NASTRAN_AERO_PATH = Path(__file__).parent.parent / "nastran-aeroelasticity" / "src"
if NASTRAN_AERO_PATH.exists():
    sys.path.insert(0, str(NASTRAN_AERO_PATH))

try:
    import numpy as np
    from pyNastran.bdf.bdf import BDF

    # Import nastran-aeroelasticity modules
    from nastran.structures.material import IsotropicMaterial, OrthotropicMaterial
    from nastran.structures.panel import IsotropicPlate
    from nastran.structures.bc import create_spcs_and_subcases, generate_bc_case
    from nastran.aero.superpanels import SuperAeroPanel5, SuperAeroPanel1
    from nastran.aero.analysis.panel_flutter import (
        PanelFlutterPistonAnalysisModel,
        PanelFlutterPistonZAEROAnalysisModel,
        PanelFlutterSubcase
    )
    from nastran.post.f06 import read_f06
    from nastran.post.flutter import get_critical_roots, join_flutter_pages, flutter_pages_to_df
    from nastran.post.plots import plot_vf_vg, plot_complex

    IMPORTS_AVAILABLE = True
    logger.info("Successfully imported nastran-aeroelasticity modules")

except ImportError as e:
    IMPORTS_AVAILABLE = False
    logger.error(f"Failed to import nastran-aeroelasticity modules: {e}")


class NastranBridge:
    """Bridge class for NASTRAN panel flutter analysis."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Ensure nastran-aeroelasticity is available
        if not IMPORTS_AVAILABLE:
            raise RuntimeError("nastran-aeroelasticity modules not available")

    def validate_environment(self) -> Dict[str, Any]:
        """Validate the analysis environment."""
        status = {
            "python_version": sys.version,
            "nastran_aero_available": IMPORTS_AVAILABLE,
            "output_directory": str(self.output_dir),
            "dependencies": {}
        }

        # Check dependencies
        try:
            import numpy
            status["dependencies"]["numpy"] = numpy.__version__
        except ImportError:
            status["dependencies"]["numpy"] = "Not available"

        try:
            import pyNastran
            status["dependencies"]["pyNastran"] = pyNastran.__version__
        except ImportError:
            status["dependencies"]["pyNastran"] = "Not available"

        try:
            import matplotlib
            status["dependencies"]["matplotlib"] = matplotlib.__version__
        except ImportError:
            status["dependencies"]["matplotlib"] = "Not available"

        return status

    def create_material(self, material_data: Dict[str, Any]) -> Any:
        """Create material object from Flutter data."""
        material_type = material_data.get("type", "isotropic")

        if material_type == "isotropic":
            return IsotropicMaterial(
                mid=material_data["id"],
                E=material_data["youngsModulus"],
                nu=material_data["poissonsRatio"],
                G=material_data["shearModulus"],
                rho=material_data["density"],
                alpha=material_data.get("thermalExpansion")
            )
        elif material_type == "orthotropic":
            return OrthotropicMaterial(
                mid=material_data["id"],
                E1=material_data["e1"],
                E2=material_data["e2"],
                nu12=material_data["nu12"],
                G12=material_data["g12"],
                rho=material_data["density"],
                alpha1=material_data.get("alpha1"),
                alpha2=material_data.get("alpha2")
            )
        else:
            raise ValueError(f"Unsupported material type: {material_type}")

    def create_plate_geometry(self, geometry_data: Dict[str, Any], material) -> IsotropicPlate:
        """Create plate geometry from Flutter data."""
        # Extract corner points
        p1 = np.array([geometry_data["p1"]["x"], geometry_data["p1"]["y"], geometry_data["p1"]["z"]])
        p2 = np.array([geometry_data["p2"]["x"], geometry_data["p2"]["y"], geometry_data["p2"]["z"]])
        p3 = np.array([geometry_data["p3"]["x"], geometry_data["p3"]["y"], geometry_data["p3"]["z"]])
        p4 = np.array([geometry_data["p4"]["x"], geometry_data["p4"]["y"], geometry_data["p4"]["z"]])

        # Create the plate
        plate = IsotropicPlate.create_plate(
            p1, p2, p3, p4,
            nspan=geometry_data["nSpan"],
            nchord=geometry_data["nChord"],
            pid=1,
            thickness=geometry_data["thickness"],
            material=material
        )

        return plate

    def create_analysis_model(self, analysis_data: Dict[str, Any], plate, aero_theory: str = "piston"):
        """Create the panel flutter analysis model."""
        params = analysis_data.get("nastranParams", {})

        # Select appropriate analysis model
        if aero_theory.lower() == "piston":
            analysis = PanelFlutterPistonAnalysisModel(plate.bdf, params=params)
        elif aero_theory.lower() == "zaero":
            analysis = PanelFlutterPistonZAEROAnalysisModel(plate.bdf, params=params)
        else:
            raise ValueError(f"Unsupported aerodynamic theory: {aero_theory}")

        return analysis

    def set_boundary_conditions(self, analysis, bc_data: Dict[str, Any], plate):
        """Set boundary conditions for the analysis."""
        bc_string = f"{bc_data['edge1'][0]}{bc_data['edge2'][0]}{bc_data['edge3'][0]}{bc_data['edge4'][0]}"

        spc_cases = {1: generate_bc_case(bc_string)}

        # Get limit nodes from plate
        nodes = plate.limit_nodes()
        # Exclude corner nodes for edges 2 and 3 as per nastran-aeroelasticity convention
        nodes[2] = nodes[2][1:-1]
        nodes[3] = nodes[3][1:-1]

        create_spcs_and_subcases(analysis, spc_cases, nodes, PanelFlutterSubcase)

    def add_aerodynamic_panels(self, analysis, aero_data: Dict[str, Any], geometry_data: Dict[str, Any]):
        """Add aerodynamic panels to the analysis."""
        # Extract geometry corner points
        p1 = np.array([geometry_data["p1"]["x"], geometry_data["p1"]["y"], geometry_data["p1"]["z"]])
        p2 = np.array([geometry_data["p2"]["x"], geometry_data["p2"]["y"], geometry_data["p2"]["z"]])
        p3 = np.array([geometry_data["p3"]["x"], geometry_data["p3"]["y"], geometry_data["p3"]["z"]])
        p4 = np.array([geometry_data["p4"]["x"], geometry_data["p4"]["y"], geometry_data["p4"]["z"]])

        for panel_data in aero_data.get("panels", []):
            theory = panel_data.get("theory", "pistonTheory")

            if theory == "pistonTheory":
                piston_type = panel_data.get("pistonTheoryType", "vanDyke").upper()
                spanel = SuperAeroPanel5(
                    panel_data["id"],
                    p1, p2, p3, p4,
                    nchord=geometry_data["nChord"],
                    nspan=geometry_data["nSpan"],
                    theory=piston_type
                )
            elif theory == "doubletLattice":
                spanel = SuperAeroPanel1(
                    panel_data["id"],
                    p1, p2, p3, p4,
                    nchord=geometry_data["nChord"],
                    nspan=geometry_data["nSpan"]
                )
            else:
                raise ValueError(f"Unsupported aerodynamic theory: {theory}")

            analysis.add_superpanel(spanel)

    def create_bdf_file(self, project_data: Dict[str, Any]) -> Tuple[str, str]:
        """Create BDF file from project data."""
        try:
            # Extract components
            material_data = project_data["material"]
            geometry_data = project_data["geometry"]
            bc_data = project_data["boundaryConditions"]
            aero_data = project_data["aerodynamicConfig"]
            analysis_params = project_data["analysisParams"]
            flow_conditions = aero_data["flowConditions"]

            # Create material
            material = self.create_material(material_data)

            # Create plate geometry
            plate = self.create_plate_geometry(geometry_data, material)

            # Determine aerodynamic theory
            first_panel = aero_data["panels"][0] if aero_data["panels"] else {}
            aero_theory = "piston" if first_panel.get("theory") == "pistonTheory" else "zaero"

            # Create analysis model
            analysis = self.create_analysis_model(analysis_params, plate, aero_theory)

            # Set global case configuration
            config = {
                'vref': flow_conditions["referenceVelocity"],
                'ref_rho': flow_conditions["referenceDensity"],
                'ref_chord': flow_conditions["referenceChord"],
                'n_modes': analysis_params["numberOfModes"],
                'frequency_limits': analysis_params["frequencyLimits"],
                'method': analysis_params["method"],
                'densities_ratio': flow_conditions["densityRatios"],
                'machs': flow_conditions["machNumbers"],
                'alphas': flow_conditions["alphas"],
                'reduced_frequencies': flow_conditions["reducedFrequencies"],
                'velocities': flow_conditions["velocities"],
            }
            analysis.set_global_case_from_dict(config)

            # Set boundary conditions
            self.set_boundary_conditions(analysis, bc_data, plate)

            # Add aerodynamic panels
            self.add_aerodynamic_panels(analysis, aero_data, geometry_data)

            # Write cards
            analysis.write_cards()

            # Generate BDF file
            model_filename = f"{project_data['name'].replace(' ', '_').lower()}"
            bdf_path = self.output_dir / f"{model_filename}.bdf"
            analysis.model.write_bdf(str(bdf_path), enddata=True)

            return str(bdf_path), model_filename

        except Exception as e:
            logger.error(f"Error creating BDF file: {e}")
            logger.error(traceback.format_exc())
            raise

    def run_nastran(self, bdf_path: str, nastran_executable: str = "nastran") -> str:
        """Run NASTRAN analysis."""
        try:
            bdf_file = Path(bdf_path)
            output_dir = bdf_file.parent

            # Change to output directory to ensure files are created there
            original_cwd = os.getcwd()
            os.chdir(output_dir)

            try:
                # Run NASTRAN
                cmd = [nastran_executable, str(bdf_file.name)]
                logger.info(f"Running NASTRAN command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )

                if result.returncode != 0:
                    error_msg = f"NASTRAN failed with return code {result.returncode}\n"
                    error_msg += f"STDOUT: {result.stdout}\n"
                    error_msg += f"STDERR: {result.stderr}"
                    raise RuntimeError(error_msg)

                # Find the F06 file
                f06_path = bdf_file.with_suffix('.f06')
                if not f06_path.exists():
                    raise FileNotFoundError(f"F06 file not found: {f06_path}")

                return str(f06_path)

            finally:
                os.chdir(original_cwd)

        except Exception as e:
            logger.error(f"Error running NASTRAN: {e}")
            raise

    def parse_f06_results(self, f06_path: str) -> Dict[str, Any]:
        """Parse F06 results file."""
        try:
            # Read F06 file
            res = read_f06(f06_path)

            results = {
                "analysisSuccessful": True,
                "flutterResults": [],
                "criticalPoints": [],
                "modalResults": [],
                "metadata": {
                    "f06Path": f06_path,
                    "totalPages": len(res.pages) if hasattr(res, 'pages') else 0
                }
            }

            # Process flutter results if available
            if hasattr(res, 'flutter') and res.flutter:
                # Join flutter pages
                pages = join_flutter_pages(res.flutter)

                # Convert to DataFrame
                df = flutter_pages_to_df(pages)

                # Convert DataFrame to list of dictionaries
                flutter_results = []
                for index, row in df.iterrows():
                    subcase, mach, point = index
                    flutter_results.append({
                        "subcase": int(subcase),
                        "machNumber": float(mach),
                        "point": int(point),
                        "index": int(row.name[2]) if len(row.name) > 2 else 0,
                        "kfreq": float(row["KFREQ"]),
                        "velocity": float(row["VELOCITY"]),
                        "damping": float(row["DAMPING"]),
                        "frequency": float(row["FREQUENCY"]),
                        "realEigenvalue": float(row["REALEIGVAL"]),
                        "imaginaryEigenvalue": float(row["IMAGEIGVAL"]),
                        "mode": int(point),
                    })

                results["flutterResults"] = flutter_results

                # Find critical points
                critical_df = get_critical_roots(df)
                critical_points = []
                for index, row in critical_df.iterrows():
                    subcase, mach, point = index
                    critical_points.append({
                        "subcase": int(subcase),
                        "machNumber": float(mach),
                        "point": int(point),
                        "kfreq": float(row["KFREQ"]),
                        "velocity": float(row["VELOCITY"]),
                        "frequency": float(row["FREQUENCY"]),
                        "damping": float(row["DAMPING"]),
                        "realEigenvalue": float(row["REALEIGVAL"]),
                        "imaginaryEigenvalue": float(row["IMAGEIGVAL"]),
                        "mode": int(point),
                        "description": f"Critical flutter point for mode {point}"
                    })

                results["criticalPoints"] = critical_points

            return results

        except Exception as e:
            logger.error(f"Error parsing F06 results: {e}")
            logger.error(traceback.format_exc())
            return {
                "analysisSuccessful": False,
                "errorMessage": str(e),
                "flutterResults": [],
                "criticalPoints": [],
                "modalResults": []
            }

    def generate_plots(self, f06_path: str, modes: Optional[List[int]] = None) -> Dict[str, str]:
        """Generate V-f and V-g plots."""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend

            # Read results
            res = read_f06(f06_path)
            pages = join_flutter_pages(res.flutter)
            df = flutter_pages_to_df(pages)

            # Generate plots
            plot_paths = {}

            # V-f and V-g plot
            fig = plot_vf_vg(df, modes=modes)
            vf_vg_path = self.output_dir / "vf_vg_plot.png"
            fig.savefig(vf_vg_path, dpi=300, bbox_inches='tight')
            plot_paths["vf_vg"] = str(vf_vg_path)

            # Complex eigenvalue plot
            fig_complex = plot_complex(df, modes=modes)
            complex_path = self.output_dir / "complex_eigenvalue_plot.png"
            fig_complex.savefig(complex_path, dpi=300, bbox_inches='tight')
            plot_paths["complex"] = str(complex_path)

            return plot_paths

        except Exception as e:
            logger.error(f"Error generating plots: {e}")
            logger.error(traceback.format_exc())
            return {}


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python nastran_bridge.py <command> [args...]")
        print("Commands:")
        print("  validate - Validate environment")
        print("  create_bdf <project_json> - Create BDF file from project JSON")
        print("  run_analysis <bdf_path> - Run NASTRAN analysis")
        print("  parse_results <f06_path> - Parse F06 results")
        sys.exit(1)

    command = sys.argv[1]

    try:
        bridge = NastranBridge()

        if command == "validate":
            result = bridge.validate_environment()
            print(json.dumps(result, indent=2))

        elif command == "create_bdf":
            if len(sys.argv) < 3:
                print("Usage: python nastran_bridge.py create_bdf <project_json>")
                sys.exit(1)

            project_json = sys.argv[2]
            with open(project_json, 'r') as f:
                project_data = json.load(f)

            bdf_path, model_name = bridge.create_bdf_file(project_data)
            result = {"bdfPath": bdf_path, "modelName": model_name}
            print(json.dumps(result))

        elif command == "run_analysis":
            if len(sys.argv) < 3:
                print("Usage: python nastran_bridge.py run_analysis <bdf_path>")
                sys.exit(1)

            bdf_path = sys.argv[2]
            f06_path = bridge.run_nastran(bdf_path)
            result = {"f06Path": f06_path}
            print(json.dumps(result))

        elif command == "parse_results":
            if len(sys.argv) < 3:
                print("Usage: python nastran_bridge.py parse_results <f06_path>")
                sys.exit(1)

            f06_path = sys.argv[2]
            results = bridge.parse_f06_results(f06_path)
            print(json.dumps(results, indent=2))

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        error_result = {"error": str(e), "traceback": traceback.format_exc()}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()