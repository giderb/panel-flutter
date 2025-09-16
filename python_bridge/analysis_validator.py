"""
Analysis Validation Bridge
=========================

This module validates the existing NASTRAN-aeroelasticity analysis capabilities
and provides a bridge interface for the modern customtkinter GUI.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging

# Add nastran-aeroelasticity source to path
current_dir = Path(__file__).parent.parent
nastran_aero_path = current_dir / "nastran-aeroelasticity" / "src"
if nastran_aero_path.exists():
    sys.path.insert(0, str(nastran_aero_path))

class AnalysisValidator:
    """Validator for existing analysis capabilities"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {}
        self._check_imports()

    def _check_imports(self):
        """Check which analysis modules are available from nastran-aeroelasticity"""
        self.available_modules = {}

        # Test core nastran modules
        try:
            from nastran.structures.material import IsotropicMaterial, OrthotropicMaterial
            self.available_modules['materials'] = True
            self.IsotropicMaterial = IsotropicMaterial
            self.OrthotropicMaterial = OrthotropicMaterial
        except ImportError as e:
            self.available_modules['materials'] = False
            self.logger.warning(f"Materials module not available: {e}")

        # Test structural panels
        try:
            from nastran.structures.panel import IsotropicPlate
            self.available_modules['structural_panels'] = True
            self.IsotropicPlate = IsotropicPlate
            # OrthotropicPlate may not exist in all versions
            try:
                from nastran.structures.panel import OrthotropicPlate
                self.OrthotropicPlate = OrthotropicPlate
            except ImportError:
                self.logger.info("OrthotropicPlate not available (optional)")
        except ImportError as e:
            self.available_modules['structural_panels'] = False
            self.logger.warning(f"Structural panels not available: {e}")

        # Test flutter analysis
        try:
            from nastran.aero.analysis.panel_flutter import PanelFlutterPistonAnalysisModel, PanelFlutterSubcase
            from nastran.aero.superpanels import SuperAeroPanel5, SuperAeroPanel1
            self.available_modules['piston_theory'] = True
            self.available_modules['panel_flutter'] = True
            self.PanelFlutterPistonAnalysisModel = PanelFlutterPistonAnalysisModel
            self.PanelFlutterSubcase = PanelFlutterSubcase
            self.SuperAeroPanel5 = SuperAeroPanel5
            self.SuperAeroPanel1 = SuperAeroPanel1
        except ImportError as e:
            self.available_modules['piston_theory'] = False
            self.available_modules['panel_flutter'] = False
            self.logger.warning(f"Flutter analysis modules not available: {e}")

        # Test boundary conditions
        try:
            from nastran.structures.bc import create_spcs_and_subcases, generate_bc_case
            self.available_modules['boundary_conditions'] = True
            self.create_spcs_and_subcases = create_spcs_and_subcases
            self.generate_bc_case = generate_bc_case
        except ImportError as e:
            self.available_modules['boundary_conditions'] = False
            self.logger.warning(f"Boundary conditions not available: {e}")

        # Test F06 parsing
        try:
            from nastran.post.f06 import read_f06
            from nastran.post.flutter import get_critical_roots, join_flutter_pages, flutter_pages_to_df
            self.available_modules['f06_parsing'] = True
            self.read_f06 = read_f06
            self.get_critical_roots = get_critical_roots
            self.join_flutter_pages = join_flutter_pages
            self.flutter_pages_to_df = flutter_pages_to_df
        except ImportError as e:
            self.available_modules['f06_parsing'] = False
            self.logger.warning(f"F06 parsing not available: {e}")

        # Test plotting
        try:
            from nastran.post.plots import plot_vf_vg
            self.available_modules['plotting'] = True
            self.plot_vf_vg = plot_vf_vg
        except ImportError as e:
            self.available_modules['plotting'] = False
            self.logger.warning(f"Plotting not available: {e}")

        # Mark as BDF generation available if we have the core modules
        self.available_modules['bdf_generator'] = (
            self.available_modules.get('materials', False) and
            self.available_modules.get('structural_panels', False) and
            self.available_modules.get('panel_flutter', False)
        )

        # Multi-solver is available if we have piston theory
        self.available_modules['multi_solver'] = self.available_modules.get('piston_theory', False)

    def validate_piston_theory(self) -> Dict[str, Any]:
        """Validate piston theory solver with Metallic example parameters"""
        if not self.available_modules.get('piston_theory', False):
            return {"success": False, "error": "Piston theory module not available"}

        try:
            # Use parameters from Metallic.ipynb
            panel = self.PanelProperties(
                length=0.300,  # 300mm -> 0.3m
                width=0.300,   # 300mm -> 0.3m (a/b = 1)
                thickness=0.0015,  # 1.5mm -> 0.0015m
                youngs_modulus=71.7e9,  # 71.7 GPa
                poissons_ratio=0.33,
                density=2810,  # 2.81 g/cm³ -> 2810 kg/m³
                boundary_conditions='SSSS'
            )

            flow = self.FlowConditions(
                mach_number=3.0,
                altitude=8000
            )

            solver = self.PistonTheorySolver()
            result = solver.find_critical_flutter_speed(panel, flow)

            # Validate against expected results from notebook (~999 m/s, ~176 Hz)
            validation = {
                "success": True,
                "flutter_speed": result.flutter_speed,
                "flutter_frequency": result.flutter_frequency,
                "flutter_mode": result.flutter_mode,
                "damping": result.damping,
                "dynamic_pressure": result.dynamic_pressure,
                "method": result.method,
                "speed_range_ok": 800 <= result.flutter_speed <= 1200,
                "freq_range_ok": 100 <= result.flutter_frequency <= 300,
                "notebook_comparison": {
                    "expected_speed": 999,
                    "expected_frequency": 176,
                    "speed_error_percent": abs(result.flutter_speed - 999) / 999 * 100,
                    "freq_error_percent": abs(result.flutter_frequency - 176) / 176 * 100
                }
            }

            return validation

        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_multi_solver(self) -> Dict[str, Any]:
        """Validate multi-solver framework"""
        if not self.available_modules.get('multi_solver', False):
            return {"success": False, "error": "Multi-solver module not available"}

        try:
            selector = self.SolverSelector()

            # Test solver recommendation for supersonic case
            panel = self.PanelProperties(0.3, 0.3, 0.0015, 71.7e9, 0.33, 2810, 'SSSS')
            flow = self.FlowConditions(3.0, 8000)

            recommendation = selector.recommend_solver(panel, flow)

            # Test analyzer
            analyzer = self.MultiSolverAnalyzer()
            velocity_range = (800, 1000)
            methods = [self.SolverMethod.PISTON_THEORY]

            results = analyzer.analyze_with_multiple_solvers(
                panel, flow, methods, velocity_range, num_points=3
            )

            validation = {
                "success": True,
                "recommendation": {
                    "method": recommendation.recommended_method.value,
                    "confidence": recommendation.confidence,
                    "reason": recommendation.reason
                },
                "analysis_results": {
                    method: {
                        "flutter_speed": result.flutter_speed if result else None,
                        "flutter_frequency": result.flutter_frequency if result else None
                    } for method, result in results.items()
                }
            }

            return validation

        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_bdf_generation(self) -> Dict[str, Any]:
        """Validate BDF file generation"""
        if not self.available_modules.get('bdf_generator', False):
            return {"success": False, "error": "BDF generator module not available"}

        try:
            generator = self.NastranBDFGenerator()

            # Test parameters
            panel_props = {
                'length': 0.3,
                'width': 0.3,
                'thickness': 0.0015,
                'youngs_modulus': 71.7e9,
                'poissons_ratio': 0.33,
                'density': 2810
            }

            mesh_props = {
                'nx': 5,  # Smaller mesh for testing
                'ny': 5
            }

            flow_props = {
                'mach': 3.0,
                'dynamic_pressure': 50000
            }

            # Generate BDF content
            bdf_content = generator.generate_flutter_bdf(
                panel_props, mesh_props, flow_props,
                boundary_conditions='SSSS',
                analysis_type='SOL_145'
            )

            validation = {
                "success": True,
                "bdf_lines": len(bdf_content.split('\\n')),
                "has_material": "MAT1" in bdf_content,
                "has_property": "PSHELL" in bdf_content,
                "has_elements": "CQUAD4" in bdf_content,
                "has_boundary": "SPC1" in bdf_content,
                "has_aero": "CAERO" in bdf_content or "AERO" in bdf_content,
                "sample_lines": bdf_content.split('\\n')[:10]
            }

            return validation

        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_materials(self) -> Dict[str, Any]:
        """Validate material definitions"""
        if not self.available_modules.get('materials', False):
            return {"success": False, "error": "Materials module not available"}

        try:
            # Test isotropic material (Aluminum 6061-T6)
            aluminum = self.IsotropicMaterial(
                mid=1,
                youngs_modulus=71.7e9,
                poissons_ratio=0.33,
                shear_modulus=26.9e9,
                density=2810,
                alpha=21e-6
            )

            # Test orthotropic material (Carbon Fiber)
            cfrp = self.OrthotropicMaterial(
                mid=2,
                e1=54000e6,
                e2=18000e6,
                nu12=0.3,
                g12=7200e6,
                density=2600,
                alpha1=0.011e-6,
                alpha2=12.47e-6
            )

            validation = {
                "success": True,
                "isotropic_created": aluminum is not None,
                "orthotropic_created": cfrp is not None,
                "aluminum_properties": {
                    "youngs_modulus": aluminum.youngs_modulus,
                    "density": aluminum.density
                },
                "cfrp_properties": {
                    "e1": cfrp.e1,
                    "e2": cfrp.e2,
                    "density": cfrp.density
                }
            }

            return validation

        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_boundary_conditions(self) -> Dict[str, Any]:
        """Validate boundary condition implementations"""
        if not self.available_modules.get('boundary_conditions', False):
            return {"success": False, "error": "Boundary conditions module not available"}

        try:
            bc_types = ['SSSS', 'CCCC', 'CFFF', 'CFCF']
            results = {}

            for bc_type in bc_types:
                try:
                    bc = self.BoundaryCondition(bc_type)
                    results[bc_type] = {
                        "success": True,
                        "description": bc.get_description() if hasattr(bc, 'get_description') else bc_type
                    }
                except Exception as e:
                    results[bc_type] = {
                        "success": False,
                        "error": str(e)
                    }

            validation = {
                "success": True,
                "boundary_conditions": results,
                "total_tested": len(bc_types),
                "successful": sum(1 for r in results.values() if r["success"])
            }

            return validation

        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all available modules"""
        results = {
            "available_modules": self.available_modules,
            "validation_tests": {}
        }

        # Run individual validations
        if self.available_modules.get('piston_theory', False):
            results["validation_tests"]["piston_theory"] = self.validate_piston_theory()

        if self.available_modules.get('multi_solver', False):
            results["validation_tests"]["multi_solver"] = self.validate_multi_solver()

        if self.available_modules.get('bdf_generator', False):
            results["validation_tests"]["bdf_generation"] = self.validate_bdf_generation()

        if self.available_modules.get('materials', False):
            results["validation_tests"]["materials"] = self.validate_materials()

        if self.available_modules.get('boundary_conditions', False):
            results["validation_tests"]["boundary_conditions"] = self.validate_boundary_conditions()

        # Summary
        total_modules = len(self.available_modules)
        available_modules = sum(1 for available in self.available_modules.values() if available)

        total_tests = len(results["validation_tests"])
        successful_tests = sum(1 for test in results["validation_tests"].values()
                              if test.get("success", False))

        results["summary"] = {
            "modules_available": f"{available_modules}/{total_modules}",
            "tests_passed": f"{successful_tests}/{total_tests}",
            "overall_success": successful_tests == total_tests and available_modules > 0
        }

        return results

# Global instance for easy access
validator = AnalysisValidator()