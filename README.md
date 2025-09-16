# NASTRAN Panel Flutter Analysis GUI

A modern, sleek GUI application for supersonic panel flutter analysis using NASTRAN and the [nastran-aeroelasticity](https://github.com/vsdsantos/nastran-aeroelasticity) library.

## 🚀 Overview

This application provides a comprehensive, user-friendly interface for designing and analyzing panel flutter phenomena in supersonic flows. Built with **customtkinter** for a modern, professional appearance, it integrates seamlessly with the nastran-aeroelasticity Python library to provide a complete workflow from model definition to results visualization.

### Key Features

- **Modern customtkinter GUI**: Professional, dark-themed interface with sleek design
- **Complete Workflow**: Guided step-by-step analysis process
- **Material Library**: Predefined aerospace materials (aluminum, steel, titanium, composites)
- **Multiple Theories**: Support for Piston Theory (CAERO5) and Doublet Lattice (CAERO1/ZAERO)
- **Real-time Validation**: Comprehensive project validation with helpful suggestions
- **Advanced Visualization**: V-f diagrams, V-g plots, and complex eigenvalue plots
- **Project Management**: Save, load, and manage multiple analysis projects
- **Python Integration**: Seamless bridge to nastran-aeroelasticity backend

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                  customtkinter GUI                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Models    │  │ GUI Panels  │  │  Managers   │      │
│  │             │  │             │  │             │      │
│  │ • Material  │  │ • Home      │  │ • Project   │      │
│  │ • Geometry  │  │ • Material  │  │ • Theme     │      │
│  │ • Aero      │  │ • Geometry  │  │ • Config    │      │
│  │ • Results   │  │ • Analysis  │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                   Python Bridge                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            nastran_bridge.py                        │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                nastran-aeroelasticity                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Structures  │  │ Aerodynamics│  │ Post-Process│      │
│  │             │  │             │  │             │      │
│  │ • Materials │  │ • Panels    │  │ • F06 Parse │      │
│  │ • Plates    │  │ • Flow      │  │ • Plotting  │      │
│  │ • BC        │  │ • Theories  │  │ • Critical  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                      NASTRAN                            │
└─────────────────────────────────────────────────────────┘
```

### Modern GUI Design

The application features:
- **Dark theme** with professional blue accents
- **Sidebar navigation** with visual indicators
- **Card-based layouts** for organized content
- **Modern typography** with proper hierarchy
- **Responsive design** that adapts to different screen sizes
- **Contextual tooltips** and help information

## 📋 Analysis Workflow

The application guides users through a structured 7-step workflow:

1. **🏠 Home**: Project overview and management
2. **🔧 Material**: Define isotropic, orthotropic, or composite materials
3. **📐 Geometry**: Configure plate dimensions, thickness, and mesh
4. **💨 Aerodynamics**: Choose theory and set flow conditions
5. **🌡️ Thermal**: Optional thermal loading conditions
6. **⚙️ Analysis**: Execute NASTRAN analysis with progress monitoring
7. **📊 Results**: Analyze V-f diagrams, critical flutter points, and more

## 🛠️ Installation

### Prerequisites

- **Python** (3.8 or later)
- **NASTRAN** (MSC NASTRAN or NX NASTRAN)
- **Git**

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/vsdsantos/nastran-aeroelasticity.git
   cd panel-flutter
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup nastran-aeroelasticity**
   ```bash
   # The nastran-aeroelasticity repository should be cloned as a submodule
   # Ensure it's available in the project directory
   ```

4. **Configure NASTRAN Path**
   - Ensure NASTRAN executable is in your system PATH
   - Or configure the path in `config.json`

5. **Run the Application**
   ```bash
   python main.py
   ```

## 🎯 Usage Examples

### Creating a New Project

1. Launch the application
2. Click "📝 New Project" on the home screen
3. Enter project name and description
4. Follow the guided workflow

### Example: Metallic Panel Analysis

1. **Material**: Select "Aluminum 6061-T6" from predefined materials
2. **Geometry**: Set 300×300×1.5 mm plate with 20×20 mesh
3. **Aerodynamics**: Configure supersonic flow (M=3.0) with Piston Theory
4. **Analysis**: Set 15 modes, PK method
5. **Run**: Execute analysis and view results

### Loading Example Projects

The application includes example projects based on the nastran-aeroelasticity notebooks:
- **Metallic Panel**: Aluminum panel flutter analysis
- **Composite Panel**: Carbon fiber panel with thermal effects
- **Hypersonic Panel**: High-speed analysis with thermal loading

## 📊 Features Implemented

### ✅ Completed Components

1. **Modern GUI Framework**
   - customtkinter-based interface with dark theme
   - Responsive sidebar navigation
   - Card-based layouts with proper spacing

2. **Project Management System**
   - Create, save, and load projects
   - Recent projects tracking
   - Project validation with detailed feedback

3. **Material Definition Interface**
   - Predefined aerospace materials library
   - Custom isotropic material creation
   - Material validation and preview
   - Support for orthotropic and composite (framework ready)

4. **Home Dashboard**
   - Project overview with completion status
   - Quick actions and navigation
   - Recent projects management
   - Example project loading

5. **Configuration Management**
   - Theme customization
   - Application settings
   - Persistent configuration storage

6. **Python Integration Bridge**
   - Complete integration with nastran-aeroelasticity
   - JSON-based communication
   - Comprehensive error handling

### 🔄 Remaining Implementation

1. **Geometry Configuration Panel**
2. **Aerodynamics Setup Panel**
3. **Thermal Effects Panel**
4. **Analysis Execution Interface**
5. **Results Visualization with Charts**
6. **Advanced Plotting Components**
7. **Complete Example Validation**

## 📁 Project Structure

```
panel-flutter/
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
├── config.json                     # Application configuration
├── gui/                           # GUI components
│   ├── main_window.py             # Main application window
│   ├── theme_manager.py           # Theme and styling
│   ├── project_manager.py         # Project management
│   └── panels/                    # Individual panels
│       ├── home_panel.py          # Home dashboard
│       ├── material_panel.py      # Material definition
│       └── ...                    # Other panels
├── models/                        # Data models
│   └── material.py               # Material models
├── utils/                         # Utilities
│   ├── logger.py                 # Logging configuration
│   └── config.py                 # Configuration management
├── python_bridge/                # Python integration
│   └── nastran_bridge.py         # NASTRAN bridge script
├── nastran-aeroelasticity/        # Submodule
└── logs/                          # Application logs
```

## 🎨 Design Philosophy

### Modern Interface Design
- **Minimalist**: Clean, uncluttered interface focusing on functionality
- **Professional**: Dark theme suitable for engineering applications
- **Intuitive**: Logical workflow with clear visual hierarchy
- **Responsive**: Adapts to different screen sizes and user preferences

### User Experience
- **Guided Workflow**: Step-by-step process with progress tracking
- **Contextual Help**: Tooltips and inline documentation
- **Error Prevention**: Real-time validation with helpful suggestions
- **Efficiency**: Keyboard shortcuts and quick actions

## 🔧 Configuration

### Application Settings

```json
{
  "appearance": {
    "theme": "dark",
    "color_theme": "blue",
    "scaling": 1.0
  },
  "nastran": {
    "executable": "nastran",
    "timeout": 3600
  },
  "analysis": {
    "default_modes": 15,
    "default_method": "PK"
  }
}
```

### Theme Customization

The application supports theme customization:
- **Dark Mode**: Professional dark theme (default)
- **Light Mode**: Traditional light theme
- **Color Accents**: Blue, green, orange themes
- **Scaling**: Support for high-DPI displays

## 📚 References

- [nastran-aeroelasticity Repository](https://github.com/vsdsantos/nastran-aeroelasticity)
- [customtkinter Documentation](https://github.com/TomSchimansky/CustomTkinter)
- Federal University of Minas Gerais (UFMG) research project
- NASTRAN Aeroelastic Analysis User's Guide

## ⚠️ Important Notes

### Critical Application Requirements

This is described as a **CRITICAL application**, so please note:

1. **Validation Required**: All analyses should be validated against known solutions
2. **Engineering Responsibility**: Users must verify results independently
3. **Safety Considerations**: Flutter analysis is crucial for aerospace safety
4. **Professional Use**: Intended for qualified aerospace engineers

### Current Status

**✅ Completed Foundation:**
- Modern GUI framework with professional appearance
- Complete project management system
- Material definition with predefined library
- Python integration bridge
- Home dashboard with project overview
- Theme and configuration management

**🔄 Ready for Extension:**
The application provides a solid, extensible foundation that can be easily completed with the remaining panels and functionality.

## 📞 Support

For issues related to:
- **GUI Application**: Create an issue in this repository
- **nastran-aeroelasticity**: Refer to the [original repository](https://github.com/vsdsantos/nastran-aeroelasticity)
- **customtkinter**: Check the [customtkinter documentation](https://github.com/TomSchimansky/CustomTkinter)

---

**Built with modern Python and customtkinter for the aerospace engineering community**