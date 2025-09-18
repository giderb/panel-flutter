"""Application configuration management."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Application configuration manager."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self._config = self._load_default_config()
        self.load()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "appearance": {
                "theme": "dark",
                "color_theme": "blue",
                "scaling": 1.0
            },
            "nastran": {
                "executable": "nastran",
                "timeout": 3600,
                "working_directory": "analysis_temp"
            },
            "project": {
                "default_directory": "projects",
                "autosave_interval": 300,
                "recent_projects_count": 10
            },
            "analysis": {
                "default_modes": 15,
                "default_method": "PK",
                "default_mach": 3.0,
                "default_velocity_range": [800000, 1200000, 50]
            },
            "plotting": {
                "dpi": 100,
                "figure_size": [10, 6],
                "save_format": "png"
            },
            "validation": {
                "strict_mode": False,
                "show_warnings": True
            }
        }

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")

    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config file: {e}")

    def _merge_config(self, file_config: Dict[str, Any]) -> None:
        """Merge file configuration with defaults."""
        def merge_dict(default: Dict, override: Dict):
            for key, value in override.items():
                if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                    merge_dict(default[key], value)
                else:
                    default[key] = value

        merge_dict(self._config, file_config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_nastran_executable(self) -> str:
        """Get NASTRAN executable path."""
        # Check for MSC NASTRAN installation
        msc_path = r"C:\MSC.Software\MSC_Nastran\20190\bin\nastran.exe"
        if os.path.exists(msc_path):
            return msc_path
        return self.get("nastran.executable", "nastran")

    def get_analysis_defaults(self) -> Dict[str, Any]:
        """Get default analysis parameters."""
        return {
            "modes": self.get("analysis.default_modes", 15),
            "method": self.get("analysis.default_method", "PK"),
            "mach": self.get("analysis.default_mach", 3.0),
            "velocity_range": self.get("analysis.default_velocity_range", [800000, 1200000, 50])
        }

    def get_appearance_settings(self) -> Dict[str, Any]:
        """Get appearance settings."""
        return {
            "theme": self.get("appearance.theme", "dark"),
            "color_theme": self.get("appearance.color_theme", "blue"),
            "scaling": self.get("appearance.scaling", 1.0)
        }