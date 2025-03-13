import tomlkit
import tomllib
from pathlib import Path


class ConfigParser:
    """Custom class to read and write TOML configuration files."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.config = {}

    def read_config(self):
        """Read and parse the TOML file."""
        if self.file_path.exists():
            with self.file_path.open("rb") as file:
                self.config = tomllib.load(file)
        else:
            self.config = {}

    def get_value(self, section, key, default=None):
        """Get a value from the config file with an optional default."""
        return self.config.get(section, {}).get(key, default)

    def set_value(self, section, key, value):
        """Set a value in the config and save it."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._write_to_file()

    def _write_to_file(self):
        """Internal method to write changes to the file."""
        with self.file_path.open("w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(self.config))
