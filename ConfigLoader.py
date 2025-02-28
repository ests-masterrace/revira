from AppConfig import AppConfig
import yaml
from yaml import Loader
import os


DEFAULT_PATHS = {
    "CONFIG": "assistant.yaml",
    "ICON": "image.png",
}


class ConfigLoader:
    """Handles loading and processing configuration"""

    @staticmethod
    def load(config_path=None):
        config = AppConfig()
        if config_path is None:
            config_path = DEFAULT_PATHS["CONFIG"]
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as stream:
                    yaml_config = yaml.load(stream, Loader=Loader)
                ConfigLoader._update_from_dict(config, yaml_config)
            except Exception as e:
                print(f"Warning: Error loading config: {e}")
        return config

    @staticmethod
    def _update_from_dict(obj, data):
        if not data or not isinstance(data, dict):
            return
        for key, value in data.items():
            if hasattr(obj, key):
                attr = getattr(obj, key)
                if hasattr(attr, "__dict__") and isinstance(value, dict):
                    ConfigLoader._update_from_dict(attr, value)
                else:
                    setattr(obj, key, value)
