from configparser import ConfigParser
from pathlib import Path

from platformdirs import user_config_dir


class SectionNotFound(Exception):
    def __init__(self, config_file_path, section_name):
        msg = f"Section {section_name} not fount in {config_file_path}"
        super().__init__(msg)


class ConfigFile:
    _CONFIG_FILE_PATH = Path(user_config_dir()) / "dymoprint.ini"
    _config_parser = None

    def __init__(self):
        config_parser = ConfigParser()
        if config_parser.read(self._CONFIG_FILE_PATH):
            self._config_parser = config_parser

    def section(self, section_name):
        """Return the given config file section as dict."""
        if self._config_parser:
            try:
                return dict(self._config_parser[section_name])
            except KeyError:
                raise SectionNotFound(self._CONFIG_FILE_PATH, section_name) from None
        return None

    @property
    def fonts_section(self):
        return self.section("FONTS")
