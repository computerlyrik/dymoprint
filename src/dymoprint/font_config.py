from configparser import ConfigParser
from pathlib import Path

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
    CONFIG_FILE = Path(user_config_dir()).joinpath("dymoprint.ini")
    if conf.read(CONFIG_FILE):
        # reading FONTS section
        if "FONTS" not in conf.sections():
            die('! config file "%s" not valid. Please change or remove.' % CONFIG_FILE)
        for style in style_to_file.keys():
            style_to_file[style] = conf.get("FONTS", style)

    return style_to_file[FLAG_TO_STYLE.get(flag, DEFAULT_FONT_STYLE)]


def parse_fonts() -> dict:
    fonts = list()
    for f in DEFAULT_FONT_DIR.iterdir():
        if f.suffix == '.ttf':
            fonts.append((f.stem, f.absolute()))
    return fonts
