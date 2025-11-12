"""Example configurations for panel flutter analysis including composite and hypersonic cases."""

from models.material import (
    IsotropicMaterial, OrthotropicMaterial, CompositeLaminate,
    CompositeLamina, PredefinedMaterials
)

class ExampleConfigurations:
    """Predefined example configurations for various panel types."""

    @staticmethod
    def get_metallic_panel():
        """Standard aluminum panel configuration."""
        return {
            "name": "Metallic Panel",
            "description": "High-strength 7050-T7451 aluminum aircraft skin panel",
            "material": PredefinedMaterials.aluminum_7050_t7451(),
            "geometry": {
                "length": 0.5,  # meters
                "width": 0.4,
                "thickness": 0.003,
                "n_chord": 10,
                "n_span": 10
            },
            "boundary_conditions": "SSSS",
            "flow": {
                "mach_number": 0.8,
                "velocity_min": 100,
                "velocity_max": 1000,
                "velocity_points": 20,
                "altitude": 10000,
                "temperature": 223.15  # -50°C at altitude
            },
            "analysis": {
                "method": "nastran",
                "n_modes": 10,
                "damping_ratio": 0.02
            }
        }

    @staticmethod
    def get_composite_panel():
        """Carbon fiber composite laminate panel configuration."""

        # Create carbon fiber material - using TF-X IM7/M91
        carbon_fiber = PredefinedMaterials.im7_m91()

        # Create quasi-isotropic laminate [0/45/-45/90]s
        laminas = []
        ply_thickness = 0.125  # mm
        layup = [0, 45, -45, 90, 90, -45, 45, 0]  # symmetric

        for i, angle in enumerate(layup):
            lamina = CompositeLamina(
                id=i+1,
                material=carbon_fiber,
                thickness=ply_thickness,
                orientation=angle
            )
            laminas.append(lamina)

        composite_material = CompositeLaminate(
            id=1,
            name="Quasi-isotropic IM7/M91 [0/45/-45/90]s",
            laminas=laminas,
            description="8-ply quasi-isotropic IM7/M91 carbon fiber laminate (TF-X)"
        )

        return {
            "name": "Composite Panel",
            "description": "IM7/M91 carbon fiber composite panel for advanced aircraft (TF-X)",
            "material": composite_material,
            "geometry": {
                "length": 0.6,  # meters
                "width": 0.5,
                "thickness": len(laminas) * ply_thickness / 1000,  # total thickness in meters
                "n_chord": 12,
                "n_span": 12
            },
            "boundary_conditions": "SSSS",
            "flow": {
                "mach_number": 0.85,
                "velocity_min": 150,
                "velocity_max": 1200,
                "velocity_points": 25,
                "altitude": 12000,
                "temperature": 216.65  # -56.5°C at altitude
            },
            "analysis": {
                "method": "nastran",
                "n_modes": 15,
                "damping_ratio": 0.01  # Lower damping for composites
            }
        }

    @staticmethod
    def get_hypersonic_panel():
        """Titanium panel for hypersonic flight conditions."""

        # Create titanium material for high temperature
        titanium = IsotropicMaterial(
            id=1,
            name="Ti-6Al-4V (High Temperature)",
            youngs_modulus=110e9,  # Slightly reduced at high temp
            poissons_ratio=0.31,
            shear_modulus=42e9,
            density=4430,
            thermal_expansion=9.5e-6,  # Higher at elevated temp
            description="Titanium alloy for hypersonic applications"
        )

        return {
            "name": "Hypersonic Panel",
            "description": "High-temperature titanium panel for hypersonic vehicles",
            "material": titanium,
            "geometry": {
                "length": 0.3,  # Smaller panel
                "width": 0.25,
                "thickness": 0.005,  # Thicker for thermal/structural requirements
                "n_chord": 15,
                "n_span": 15
            },
            "boundary_conditions": "CCCC",  # Clamped due to thermal stresses
            "flow": {
                "mach_number": 5.0,  # Hypersonic
                "velocity_min": 500,
                "velocity_max": 2500,
                "velocity_points": 30,
                "altitude": 30000,  # High altitude
                "temperature": 500  # Elevated temperature due to aerodynamic heating (227°C)
            },
            "analysis": {
                "method": "nastran",
                "n_modes": 20,  # More modes for complex behavior
                "damping_ratio": 0.03,
                "include_thermal": True,
                "thermal_stress": True
            }
        }

    @staticmethod
    def get_sandwich_panel():
        """Honeycomb sandwich panel configuration."""

        # Face sheet material (aluminum)
        face_sheet = IsotropicMaterial(
            id=1,
            name="Aluminum 2024-T3 Face Sheet",
            youngs_modulus=73.1e9,
            poissons_ratio=0.33,
            shear_modulus=28e9,
            density=2780,
            description="Face sheet material"
        )

        # Equivalent core properties (honeycomb)
        core = OrthotropicMaterial(
            id=2,
            name="Nomex Honeycomb Core",
            e1=0.001e9,  # Very low in-plane stiffness
            e2=0.001e9,
            nu12=0.01,
            g12=0.0005e9,
            g1z=0.050e9,  # Transverse shear stiffness
            g2z=0.030e9,
            density=48,  # Low density honeycomb
            description="Honeycomb core material"
        )

        return {
            "name": "Sandwich Panel",
            "description": "Lightweight honeycomb sandwich panel",
            "material": face_sheet,  # Simplified as single material
            "geometry": {
                "length": 0.8,
                "width": 0.6,
                "thickness": 0.025,  # Total thickness including core
                "n_chord": 10,
                "n_span": 10
            },
            "boundary_conditions": "SSSS",
            "flow": {
                "mach_number": 0.7,
                "velocity_min": 100,
                "velocity_max": 800,
                "velocity_points": 20,
                "altitude": 8000,
                "temperature": 236.15
            },
            "analysis": {
                "method": "nastran",
                "n_modes": 12,
                "damping_ratio": 0.025
            }
        }

    @staticmethod
    def get_space_panel():
        """Space structure panel with extreme conditions."""

        # Create specialized composite for space
        space_composite = OrthotropicMaterial(
            id=1,
            name="M55J/Cyanate Ester",
            e1=540e9,  # Ultra-high modulus carbon fiber
            e2=7e9,
            nu12=0.25,
            g12=3.5e9,
            density=1650,
            alpha1=-1.1e-6,  # Near-zero CTE
            alpha2=30e-6,
            description="Ultra-high modulus space composite"
        )

        return {
            "name": "Space Panel",
            "description": "Ultra-light panel for space structures",
            "material": space_composite,
            "geometry": {
                "length": 1.0,
                "width": 0.8,
                "thickness": 0.002,  # Very thin
                "n_chord": 20,
                "n_span": 20
            },
            "boundary_conditions": "FFFF",  # Free-free for space structures
            "flow": {
                "mach_number": 0.0,  # No aerodynamic flow in space
                "velocity_min": 0,
                "velocity_max": 100,  # For deployment dynamics
                "velocity_points": 10,
                "altitude": 400000,  # Orbit altitude
                "temperature": 120  # Temperature cycling (-150°C to +120°C)
            },
            "analysis": {
                "method": "nastran",
                "n_modes": 25,
                "damping_ratio": 0.001,  # Very low damping in vacuum
                "include_thermal": True
            }
        }

    @staticmethod
    def get_all_examples():
        """Get all example configurations."""
        return {
            "metallic": ExampleConfigurations.get_metallic_panel(),
            "composite": ExampleConfigurations.get_composite_panel(),
            "hypersonic": ExampleConfigurations.get_hypersonic_panel(),
            "sandwich": ExampleConfigurations.get_sandwich_panel(),
            "space": ExampleConfigurations.get_space_panel()
        }

    @staticmethod
    def apply_configuration(project_manager, config_name):
        """Apply a configuration to the current project."""

        examples = ExampleConfigurations.get_all_examples()

        if config_name not in examples:
            raise ValueError(f"Unknown configuration: {config_name}")

        config = examples[config_name]

        if not project_manager.current_project:
            # Create new project
            project = project_manager.create_project(
                name=config["name"],
                description=config["description"]
            )
        else:
            project = project_manager.current_project

        # Apply configuration
        project.material = config["material"]
        project.geometry = config["geometry"]
        project.boundary_conditions = config["boundary_conditions"]

        # Set aerodynamic configuration
        project.aerodynamic_config = {
            "flow_conditions": config["flow"],
            "theory": "doublet_lattice" if config["flow"]["mach_number"] < 1.0 else "piston_theory"
        }

        # Set analysis parameters
        project.analysis_params = config["analysis"]

        # Save project
        project_manager.save_project(project)

        return project