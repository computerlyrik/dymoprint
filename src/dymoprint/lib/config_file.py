import logging
from configparser import ConfigParser
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from platformdirs import user_config_dir

logger = logging.getLogger(__name__)


def get_config_file() -> Path:
    return Path(user_config_dir()) / "dymoprint.ini"


@lru_cache
def get_config() -> ConfigParser:
    config_parser = ConfigParser()
    file_to_read = get_config_file()
    if config_parser.read(file_to_read):
        logger.debug(f"Read config file: {file_to_read}")
    else:
        logger.debug(f"Config file not found: {file_to_read}")
    return config_parser


def get_config_section(section_name) -> Optional[Dict[str, Any]]:
    config = get_config()
    if section_name not in config:
        return None
    return dict(config[section_name])
