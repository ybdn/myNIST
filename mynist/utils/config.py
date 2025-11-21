"""Configuration management for myNIST application."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Application configuration manager."""

    DEFAULT_CONFIG = {
        'ui': {
            'window_width': 1400,
            'window_height': 800,
            'panel_sizes': [300, 550, 550],
            'theme': 'Fusion',
        },
        'files': {
            'last_opened_dir': str(Path.home()),
            'last_export_dir': str(Path.home()),
        },
        'export': {
            'signa_multiple': {
                'delete_fields': [215],
                'replace_fields': {
                    217: "11707"
                }
            }
        },
        'logging': {
            'level': 'INFO',
            'enabled': True,
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file (default: ~/.mynist/config.json)
        """
        if config_path is None:
            config_dir = Path.home() / '.mynist'
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / 'config.json'
        else:
            self.config_path = Path(config_path)

        self.config: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Load configuration from file or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                # Merge with defaults for missing keys
                self._merge_defaults()
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            # Use defaults
            self.config = self.DEFAULT_CONFIG.copy()

    def save(self):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path (e.g., 'ui.window_width')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path (e.g., 'ui.window_width')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def _merge_defaults(self):
        """Merge loaded config with defaults for missing keys."""
        def merge_dict(default: dict, loaded: dict) -> dict:
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = merge_dict(self.DEFAULT_CONFIG, self.config)


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get singleton configuration instance.

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
