from appdirs import user_config_dir
import os

from .constants import DEFAULT_FONT_STYLE, FLAG_TO_STYLE
import dymoprint_fonts

try:
    from configparser import SafeConfigParser
except ImportError:  # Python 2
    from ConfigParser import SafeConfigParser


def font_filename(flag):
    # The directory of the dymoprints_fonts package
    DEFAULT_FONT_DIR = os.path.dirname(dymoprint_fonts.__file__)

    # Default values
    style_to_file = {
        "regular": os.path.join(DEFAULT_FONT_DIR, "Carlito-Regular.ttf"),
        "bold": os.path.join(DEFAULT_FONT_DIR, "Carlito-Bold.ttf"),
        "italic": os.path.join(DEFAULT_FONT_DIR, "Carlito-Italic.ttf"),
        "narrow": os.path.join(DEFAULT_FONT_DIR, "Carlito-BoldItalic.ttf"),
    }

    conf = SafeConfigParser(style_to_file)
    CONFIG_FILE = os.path.join(user_config_dir(), "dymoprint.ini")
    if conf.read(CONFIG_FILE):
        # reading FONTS section
        if not "FONTS" in conf.sections():
            die('! config file "%s" not valid. Please change or remove.' % conf_file)
        for style in style_to_file.keys():
            style_to_file[style] = conf.get("FONTS", style)

    return style_to_file[FLAG_TO_STYLE.get(flag, DEFAULT_FONT_STYLE)]
