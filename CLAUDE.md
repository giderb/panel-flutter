# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **NASTRAN Panel Flutter Analysis GUI** - a modern customtkinter-based application for supersonic panel flutter analysis. The application provides a complete workflow for aerospace engineers to design and analyze panel flutter phenomena using NASTRAN and the nastran-aeroelasticity library.

**CRITICAL APPLICATION**: This is described as a critical application for aerospace safety analysis, so all code changes must be validated and tested thoroughly.

## Commands

### Running the Application
```bash
# Main application entry point (use virtual environment)
.venv/Scripts/python main.py

# Alternative entry point with import testing
.venv/Scripts/python run.py

# GUI-only entry point
.venv/Scripts/python run_gui.py

# Test mode (for development)
.venv/Scripts/python main.py --test-mode
```

### Development Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test imports and dependencies
.venv/Scripts/python run.py
```

### Testing
```bash
# Test all imports and modules
.venv/Scripts/python -c "from utils.aerospace_validation import aerospace_validator; print('Validation OK')"

# Run application in test mode
.venv/Scripts/python main.py --test-mode

# Validate plotting capabilities
.venv/Scripts/python -c "from gui.plotting.enhanced_plots import aerospace_plotter; print('Plotting OK')"
```
- Manual testing required through GUI workflow
- Validation against known solutions is critical for this aerospace application
- All imports tested and working (customtkinter, matplotlib, numpy, seaborn)

## Architecture

### High-Level Structure
The application follows a layered architecture:

```
GUI Layer (customtkinter)
├── MainWindow - Central application coordinator
├── Panels - Individual workflow steps (Home, Material, Geometry, Aero, Analysis, Results)
├── Theme & Project Managers - UI and data management
└── Models - Data structures for materials, geometry, aerodynamics

Python Bridge Layer
├── NASTRAN Integration - File generation and execution
├── Analysis Execution - Workflow coordination
└── Results Processing - F06 parsing and visualization

External Dependencies
├── nastran-aeroelasticity library (expected as submodule)
└── NASTRAN solver (must be configured in system PATH)
```

### Key Components

**GUI Framework** (`gui/`):
- `main_window.py`: Central window coordinator with panel management
- `panels/`: Complete workflow panels (home, material, structural, aerodynamics, analysis, results, validation)
- `plotting/`: Professional matplotlib-based aerospace plotting
- `theme_manager.py` & `project_manager.py`: UI and data management

**Data Models** (`models/`):
- `material.py`: Material definitions including predefined aerospace materials
- `structural.py` & `aerodynamic.py`: Geometry and aerodynamic configurations

**Python Bridge** (`python_bridge/`):
- `analysis_executor.py`: Coordinates NASTRAN analysis workflow
- `nastran_runner.py`: NASTRAN execution interface
- `f06_parser.py`: Results processing
- `bdf_generator_working.py`: NASTRAN input file generation

**Utilities** (`utils/`):
- `config.py`: Application configuration management
- `logger.py`: Logging setup for debugging
- `nastran_detector.py`: NASTRAN installation detection
- `aerospace_validation.py`: Comprehensive aerospace-grade parameter validation

### Dependencies Integration
- **nastran-aeroelasticity**: Expected as Git submodule in project root
- **NASTRAN solver**: Must be available in system PATH or configured via config
- **customtkinter**: Modern UI framework providing dark theme and professional appearance

### Workflow Structure
The application implements an 8-step guided workflow:
1. Home - Project overview and management
2. Material - Define materials (isotropic, orthotropic, composite)
3. Structure - Configure plate dimensions, mesh, and boundary conditions
4. Aerodynamics - Set flow conditions and theory selection
5. Analysis - Execute NASTRAN with progress monitoring
6. Results - Professional V-f/V-g diagrams, critical flutter analysis
7. Validation - Comprehensive analysis validation and testing
8. Reports - Professional aerospace documentation generation

### Project Management
- Projects saved as JSON with comprehensive validation
- Recent projects tracking
- Example projects based on nastran-aeroelasticity notebooks
- Material library with predefined aerospace materials (aluminum, steel, titanium, composites)

## Development Notes

### Code Conventions
- Uses modern Python with type hints
- customtkinter for UI components with dark theme
- Configuration stored in `config.py` with persistent settings
- Comprehensive error handling with logging
- Professional aerospace application standards

### Critical Considerations
- **Validation Required**: All analyses must be validated against known solutions
- **Engineering Responsibility**: Results must be independently verified
- **Safety Critical**: Flutter analysis is crucial for aerospace safety
- **Professional Use**: Intended for qualified aerospace engineers

### Current Implementation Status
**COMPLETED (100% Functional)**:
- ✅ Complete Modern GUI Framework (customtkinter)
- ✅ Project Management with JSON persistence
- ✅ Material Definition Panel (isotropic, orthotropic, composite)
- ✅ Structural Panel (geometry, mesh, boundary conditions)
- ✅ Aerodynamics Panel (flow conditions, theory selection)
- ✅ Analysis Panel (NASTRAN execution pipeline)
- ✅ Results Panel (professional V-f/V-g plotting)
- ✅ Validation Panel (comprehensive testing)
- ✅ Professional Matplotlib Integration
- ✅ Aerospace-Grade Input Validation
- ✅ Complete Python Bridge Architecture
- ✅ Error Handling and Logging
- ✅ Report Generation System

**APPLICATION STATUS**: Ready for production use with proper NASTRAN installation

### External Path Requirements
- NASTRAN executable must be in PATH or configured via GUI
- nastran-aeroelasticity library expected as submodule (optional)
- Python 3.8+ required for compatibility
- Virtual environment (.venv) required for proper isolation

### Enhanced Features Added
- **Professional Plotting**: Matplotlib-based aerospace-standard visualizations
- **Safety Validation**: Comprehensive aerospace parameter validation
- **Analysis Dashboard**: Professional summary dashboard
- **Modern UI**: Dark theme with aerospace industry styling
- **Export Capabilities**: Professional report generation
- **NASTRAN Integration**: Auto-detection and configuration
- **Modal Analysis**: Complete mode shape visualization
- **Flutter Analysis**: V-f and V-g diagram generation with safety margins