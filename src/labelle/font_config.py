import os
import re
import warnings
from configparser import ConfigParser

from appdirs import user_config_dir

from .constants import DEFAULT_FONT_DIR, DEFAULT_FONT_STYLE, FLAG_TO_STYLE
from .utils import die


def font_filename(flag):
    # Default values
    style_to_file = {
        "regular": str(DEFAULT_FONT_DIR / "Carlito-Regular.ttf"),
        "bold": str(DEFAULT_FONT_DIR / "Carlito-Bold.ttf"),
        "italic": str(DEFAULT_FONT_DIR / "Carlito-Italic.ttf"),
        "narrow": str(DEFAULT_FONT_DIR / "Carlito-BoldItalic.ttf"),
    }

    conf = ConfigParser(style_to_file)
    old_config_file = os.path.join(user_config_dir(), "dymoprint.ini")
    config_file = os.path.join(user_config_dir(), "labelle.ini")
    if os.path.exists(old_config_file) and not os.path.exists(config_file):
        warnings.warn(
            f"Old config file found at {old_config_file}. "
            f"Please rename it to {config_file}"
        )
        config_file = old_config_file
    if conf.read(config_file):
        # reading FONTS section
        if "FONTS" not in conf.sections():
            die('! config file "%s" not valid. Please change or remove.' % config_file)
        for style in style_to_file.keys():
            style_to_file[style] = conf.get("FONTS", style)

    return style_to_file[FLAG_TO_STYLE.get(flag, DEFAULT_FONT_STYLE)]


def parse_fonts() -> dict:
    fonts = list()
    for f in os.listdir(DEFAULT_FONT_DIR):
        m = re.match(r"(.*-.*).ttf", f)
        if m:
            fonts.append((m.group(1), os.path.join(DEFAULT_FONT_DIR, f)))
    return fonts
