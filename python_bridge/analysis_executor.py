"""
Analysis Executor - GUI Bridge
===============================
Bridges the GUI with the validated flutter analysis system.
Replaces python_bridge/analysis_executor.py
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging
import numpy as np
import time
from dataclasses import dataclass

# Add the validated modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the validated flutter analysis components
try:
    from .flutter_analyzer import FlutterAnalyzer, PanelProperties, FlowConditions as FlowCond
    from .pynastran_bdf_generator import PyNastranBDFGenerator, create_pynastran_flutter_bdf
    from .nastran_interface import F06Parser
    from .integrated_analysis_executor import IntegratedFlutterExecutor
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import analysis modules: {e}")
    ANALYSIS_AVAILABLE = False

# Import GUI models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.material import IsotropicMaterial, OrthotropicMaterial
from models.structural import PanelGeometry, BoundaryCondition
from models.aerodynamic import FlowConditions, AerodynamicModel


class AnalysisExecutor:
    """
    Main analysis executor for the GUI
    Provides a clean interface between GUI and validated flutter analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if ANALYSIS_AVAILABLE:
            self.flutter_executor = IntegratedFlutterExecutor()
            self.logger.info("Validated flutter analysis system initialized")
        else:
            self.flutter_executor = None
            self.logger.warning("Flutter analysis modules not available - using fallback")
    
    def run_analysis(self, structural_model: Any, aerodynamic_model: Any,
                    config: Dict[str, Any], 
                    progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Run flutter analysis from GUI models
        
        Args:
            structural_model: GUI structural model
            aerodynamic_model: GUI aerodynamic model  
            config: Analysis configuration
            progress_callback: Progress reporting callback
            
        Returns:
            Analysis results dictionary
        """
        
        if not ANALYSIS_AVAILABLE:
            return self._run_fallback_analysis(structural_model, aerodynamic_model, config, progress_callback)
        
        try:
            # Use the validated flutter executor
            return self.flutter_executor.execute_analysis(
                structural_model,
                aerodynamic_model,
                config,
                progress_callback
            )
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'converged': False
            }
    
    def run_nastran_analysis(self, structural_model: Any, aerodynamic_model: Any,
                            config: Dict[str, Any],
                            progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run NASTRAN-specific analysis
        """
        
        if not ANALYSIS_AVAILABLE:
            return {'success': False, 'error': 'NASTRAN analysis not available'}
        
        # Set config to use NASTRAN
        nastran_config = config.copy()
        nastran_config['use_nastran'] = True
        nastran_config['execute_nastran'] = True
        
        return self.run_analysis(
            structural_model,
            aerodynamic_model,
            nastran_config,
            progress_callback
        )
    
    def generate_bdf_only(self, structural_model: Any, aerodynamic_model: Any,
                         config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate BDF file without running analysis
        """
        
        if not ANALYSIS_AVAILABLE:
            return {'success': False, 'error': 'BDF generation not available'}
        
        try:
            # Convert models
            panel = self._convert_structural_model(structural_model)
            flow = self._convert_aerodynamic_model(aerodynamic_model)

            # Generate BDF using pyNastran generator
            working_dir = config.get('working_dir', '.')
            generator = PyNastranBDFGenerator(output_dir=working_dir)
            bdf_path = Path(working_dir) / 'flutter_analysis.bdf'

            # Create config dict for pyNastran generator
            bdf_config = {
                'panel_length': panel.length,
                'panel_width': panel.width,
                'thickness': panel.thickness,
                'nx': config.get('mesh_nx', 20),
                'ny': config.get('mesh_ny', 20),
                'youngs_modulus': panel.youngs_modulus,
                'poissons_ratio': panel.poissons_ratio,
                'density': panel.density,
                'mach_number': flow.mach_number,
                'velocity': getattr(flow, 'velocity', 1000),
                'boundary_conditions': panel.boundary_conditions,
                'n_modes': config.get('n_modes', 20),
                'output_filename': bdf_path.name
            }

            bdf_file_path = create_pynastran_flutter_bdf(bdf_config, working_dir)

            # Read BDF content for return
            with open(bdf_file_path, 'r') as f:
                bdf_content = f.read()
            
            return {
                'success': True,
                'bdf_file': str(bdf_file_path),
                'bdf_content': bdf_content,
                'bdf_lines': len(bdf_content.split('\n'))
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_analysis(self, structural_model: Any, aerodynamic_model: Any) -> Dict[str, Any]:
        """
        Validate the analysis setup
        """
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check structural model
        if not hasattr(structural_model, 'material') or not structural_model.material:
            validation['errors'].append("No material defined")
            validation['valid'] = False
        
        if not hasattr(structural_model, 'panel') or not structural_model.panel:
            validation['errors'].append("No panel geometry defined")
            validation['valid'] = False
        else:
            panel = structural_model.panel
            if panel.thickness <= 0:
                validation['errors'].append("Panel thickness must be positive")
                validation['valid'] = False
            if panel.thickness / min(panel.length, panel.width) > 0.1:
                validation['warnings'].append("Thick panel - plate theory may not be accurate")
        
        # Check aerodynamic model
        if not hasattr(aerodynamic_model, 'flow_conditions') or not aerodynamic_model.flow_conditions:
            validation['errors'].append("No flow conditions defined")
            validation['valid'] = False
        else:
            flow = aerodynamic_model.flow_conditions
            if flow.mach_number <= 0:
                validation['errors'].append("Mach number must be positive")
                validation['valid'] = False
            if 0.8 <= flow.mach_number <= 1.2:
                validation['warnings'].append("Transonic regime - results may be less accurate")
            if flow.mach_number > 5:
                validation['warnings'].append("Hypersonic flow - additional physics may be needed")
        
        return validation
    
    def _convert_structural_model(self, model: Any) -> 'PanelProperties':
        """Convert GUI structural model to analysis format"""
        
        # Extract material properties
        material = getattr(model, 'material', None)
        if material:
            E = getattr(material, 'youngs_modulus', 71.7e9)
            nu = getattr(material, 'poissons_ratio', 0.33)
            rho = getattr(material, 'density', 2810)
        else:
            # Default aluminum
            E, nu, rho = 71.7e9, 0.33, 2810
        
        # Extract geometry
        panel = getattr(model, 'panel', None)
        if panel:
            length = getattr(panel, 'length', 0.3)
            width = getattr(panel, 'width', 0.3)
            thickness = getattr(panel, 'thickness', 0.0015)
        else:
            length, width, thickness = 0.3, 0.3, 0.0015
        
        # Extract boundary conditions
        bc = getattr(model, 'boundary_condition', 'SSSS')
        if hasattr(bc, 'value'):
            bc = bc.value
        
        return PanelProperties(
            length=float(length),
            width=float(width),
            thickness=float(thickness),
            youngs_modulus=float(E),
            poissons_ratio=float(nu),
            density=float(rho),
            boundary_conditions=str(bc)
        )
    
    def _convert_aerodynamic_model(self, model: Any) -> 'FlowCond':
        """Convert GUI aerodynamic model to analysis format"""
        
        flow = getattr(model, 'flow_conditions', None)
        if flow:
            return FlowCond(
                mach_number=float(getattr(flow, 'mach_number', 2.0)),
                altitude=float(getattr(flow, 'altitude', 10000)),
                temperature=getattr(flow, 'temperature', None),
                pressure=getattr(flow, 'pressure', None),
                density=getattr(flow, 'density', None)
            )
        else:
            return FlowCond(mach_number=2.0, altitude=10000)
    
    def _run_fallback_analysis(self, structural_model: Any, aerodynamic_model: Any,
                              config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Fallback analysis when validated modules not available
        Returns safe placeholder results for GUI testing
        """
        
        self.logger.warning("Using fallback analysis - not for production use")
        
        if progress_callback:
            progress_callback("Running fallback analysis...", 0.5)
        
        # Extract basic parameters
        panel = getattr(structural_model, 'panel', None)
        flow = getattr(aerodynamic_model, 'flow_conditions', None)
        
        if panel and flow:
            # Simple frequency estimate
            thickness = getattr(panel, 'thickness', 0.0015)
            length = getattr(panel, 'length', 0.3)
            E = getattr(getattr(structural_model, 'material', None), 'youngs_modulus', 71.7e9)
            rho = getattr(getattr(structural_model, 'material', None), 'density', 2810)
            
            # First mode frequency estimate
            D = E * thickness**3 / 12
            freq = (np.pi**2 / 2) * np.sqrt(D / (rho * thickness)) * (2 / length)**2 / (2 * np.pi)
            
            # Flutter speed estimate (very rough)
            M = getattr(flow, 'mach_number', 2.0)
            flutter_speed = 1000 * M / 2  # Very rough estimate
        else:
            freq = 150.0
            flutter_speed = 1000.0
        
        if progress_callback:
            progress_callback("Analysis complete (fallback)", 1.0)
        
        return {
            'success': True,
            'method': 'Fallback (Not Validated)',
            'converged': False,
            'critical_flutter_speed': flutter_speed,
            'critical_flutter_frequency': freq,
            'critical_flutter_mode': 1,
            'warning': 'Using fallback analysis - install validated modules for real results',
            'configuration': {
                'panel_dimensions': 'Unknown',
                'material': 'Unknown',
                'boundary_conditions': 'Unknown',
                'mach_number': 2.0
            },
            'validation_status': 'NOT VALIDATED - FALLBACK MODE',
            'flutter_data': {
                'velocities': list(range(100, 2000, 100)),
                'damping': [-0.05] * 19,
                'frequencies': [freq] * 19
            }
        }


# Singleton instance
executor = AnalysisExecutor()

# Convenience functions for backward compatibility
def run_analysis(*args, **kwargs):
    """Run flutter analysis"""
    return executor.run_analysis(*args, **kwargs)

def run_nastran_analysis(*args, **kwargs):
    """Run NASTRAN analysis"""
    return executor.run_nastran_analysis(*args, **kwargs)

def validate_analysis(*args, **kwargs):
    """Validate analysis setup"""
    return executor.validate_analysis(*args, **kwargs)

def generate_bdf(*args, **kwargs):
    """Generate BDF file"""
    return executor.generate_bdf_only(*args, **kwargs)
