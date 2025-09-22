"""Project management for panel flutter analysis projects."""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from models.material import IsotropicMaterial, OrthotropicMaterial, CompositeLaminate, material_from_dict

@dataclass
class Project:
    """Panel flutter analysis project."""
    id: str
    name: str
    created_at: datetime
    modified_at: datetime
    description: Optional[str] = None

    # Analysis components
    material: Optional[Any] = None
    geometry: Optional[Dict[str, Any]] = None
    boundary_conditions: Optional[str] = None
    aerodynamic_config: Optional[Dict[str, Any]] = None
    analysis_params: Optional[Dict[str, Any]] = None
    # Results
    results: Optional[Dict[str, Any]] = None

    # File paths
    project_directory: Optional[str] = None
    bdf_file_path: Optional[str] = None
    f06_file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization."""
        data = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "description": self.description,
            "geometry": self.geometry,
            "boundary_conditions": self.boundary_conditions,
            "aerodynamic_config": self.aerodynamic_config,
            "analysis_params": self.analysis_params,
            "results": self.results,
            "project_directory": self.project_directory,
            "bdf_file_path": self.bdf_file_path,
            "f06_file_path": self.f06_file_path
        }

        # Handle material serialization
        if self.material:
            if hasattr(self.material, 'to_dict'):
                data["material"] = self.material.to_dict()
            else:
                data["material"] = self.material

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary."""
        # Parse datetime fields
        created_at = datetime.fromisoformat(data["created_at"])
        modified_at = datetime.fromisoformat(data["modified_at"])

        # Parse material
        material = None
        if data.get("material"):
            try:
                material = material_from_dict(data["material"])
            except Exception:
                material = data["material"]  # Keep as dict if parsing fails

        return cls(
            id=data["id"],
            name=data["name"],
            created_at=created_at,
            modified_at=modified_at,
            description=data.get("description"),
            material=material,
            geometry=data.get("geometry"),
            boundary_conditions=data.get("boundary_conditions"),
            aerodynamic_config=data.get("aerodynamic_config"),
            analysis_params=data.get("analysis_params"),
            results=data.get("results"),
            project_directory=data.get("project_directory"),
            bdf_file_path=data.get("bdf_file_path"),
            f06_file_path=data.get("f06_file_path")
        )

    def is_configured(self) -> bool:
        """Check if project is fully configured for analysis."""
        return all([
            self.material is not None,
            self.geometry is not None,
            self.boundary_conditions is not None,
            self.aerodynamic_config is not None,
            self.analysis_params is not None
        ])

    def get_completion_percentage(self) -> float:
        """Get project completion percentage."""
        components = [
            self.material,
            self.geometry,
            self.boundary_conditions,
            self.aerodynamic_config,
            self.analysis_params
        ]
        completed = sum(1 for comp in components if comp is not None)
        return (completed / len(components)) * 100

    def validate(self) -> List[str]:
        """Validate project configuration and return list of errors."""
        errors = []

        if not self.material:
            errors.append("Material definition is required")

        if not self.geometry:
            errors.append("Plate geometry is required")
        elif self.geometry:
            if self.geometry.get("thickness", 0) <= 0:
                errors.append("Plate thickness must be positive")
            if self.geometry.get("n_chord", 0) < 2 or self.geometry.get("n_span", 0) < 2:
                errors.append("Mesh density too low (minimum 2 elements per direction)")

        if not self.boundary_conditions:
            errors.append("Boundary conditions are required")

        if not self.aerodynamic_config:
            errors.append("Aerodynamic configuration is required")
        elif self.aerodynamic_config:
            flow_conditions = self.aerodynamic_config.get("flow_conditions", {})
            if not flow_conditions.get("mach_numbers"):
                errors.append("At least one Mach number is required")
            if not flow_conditions.get("velocities"):
                errors.append("Analysis velocities are required")

        if not self.analysis_params:
            errors.append("Analysis parameters are required")

        return errors

class ProjectManager:
    """Manages panel flutter analysis projects."""

    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(exist_ok=True)
        self.current_project: Optional[Project] = None
        self.recent_projects: List[Project] = []
        self._load_recent_projects()

    def create_project(self, name: str, description: str = "") -> Project:
        """Create a new project."""
        now = datetime.now()
        project_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_').lower()}"

        project = Project(
            id=project_id,
            name=name,
            created_at=now,
            modified_at=now,
            description=description if description else None
        )

        # Create project directory
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(exist_ok=True)
        project.project_directory = str(project_dir)

        self.current_project = project
        self._add_to_recent(project)

        return project

    def save_project(self, project: Optional[Project] = None) -> bool:
        """Save project to file."""
        if project is None:
            project = self.current_project

        if not project:
            return False

        try:
            project.modified_at = datetime.now()
            project_file = self.projects_dir / f"{project.id}.json"

            with open(project_file, 'w') as f:
                json.dump(project.to_dict(), f, indent=2, default=str)

            self._add_to_recent(project)
            return True

        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    def load_project(self, project_file: str) -> Optional[Project]:
        """Load project from file."""
        try:
            project_path = Path(project_file)
            if not project_path.exists():
                return None

            with open(project_path, 'r') as f:
                data = json.load(f)

            project = Project.from_dict(data)
            self.current_project = project
            self._add_to_recent(project)

            return project

        except Exception as e:
            print(f"Error loading project: {e}")
            return None

    def get_recent_projects(self) -> List[Project]:
        """Get list of recent projects."""
        return self.recent_projects[:10]  # Return only the 10 most recent

    def _add_to_recent(self, project: Project):
        """Add project to recent projects list."""
        # Remove if already in list
        self.recent_projects = [p for p in self.recent_projects if p.id != project.id]
        # Add to beginning
        self.recent_projects.insert(0, project)
        # Keep only last 10
        self.recent_projects = self.recent_projects[:10]
        # Save recent projects
        self._save_recent_projects()

    def _load_recent_projects(self):
        """Load recent projects from file."""
        recent_file = self.projects_dir / "recent_projects.json"
        if not recent_file.exists():
            return

        try:
            with open(recent_file, 'r') as f:
                data = json.load(f)

            self.recent_projects = []
            for project_data in data:
                try:
                    project = Project.from_dict(project_data)
                    # Check if project file still exists
                    project_file = self.projects_dir / f"{project.id}.json"
                    if project_file.exists():
                        self.recent_projects.append(project)
                except Exception:
                    continue  # Skip corrupted entries

        except Exception:
            self.recent_projects = []

    def _save_recent_projects(self):
        """Save recent projects to file."""
        recent_file = self.projects_dir / "recent_projects.json"
        try:
            data = [project.to_dict() for project in self.recent_projects]
            with open(recent_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass  # Fail silently

    def delete_project(self, project: Project) -> bool:
        """Delete a project and its files."""
        try:
            # Remove project file
            project_file = self.projects_dir / f"{project.id}.json"
            if project_file.exists():
                project_file.unlink()

            # Remove from recent projects
            self.recent_projects = [p for p in self.recent_projects if p.id != project.id]
            self._save_recent_projects()

            # Clear current project if it's the one being deleted
            if self.current_project and self.current_project.id == project.id:
                self.current_project = None

            # Remove project directory if it exists
            if project.project_directory:
                project_dir = Path(project.project_directory)
                if project_dir.exists() and project_dir.is_dir():
                    import shutil
                    shutil.rmtree(project_dir)

            return True

        except Exception as e:
            print(f"Error deleting project: {e}")
            return False