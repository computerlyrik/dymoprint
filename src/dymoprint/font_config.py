from configparser import ConfigParser
from pathlib import Path

from platformdirs import user_config_dir

from ._vendor.matplotlib import font_manager
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
            die(f'! config file "{CONFIG_FILE}" not valid. Please change or remove.')
        for style in style_to_file:
            style_to_file[style] = conf.get("FONTS", style)

    return style_to_file[FLAG_TO_STYLE.get(flag, DEFAULT_FONT_STYLE)]


def available_fonts():
    fonts = [f for f in DEFAULT_FONT_DIR.iterdir() if f.suffix == '.ttf']
    fonts.extend(Path(f) for f in font_manager.findSystemFonts())
    return sorted(fonts, key=lambda f: f.stem.lower())


def parse_fonts():
    return ((f.stem, str(f.absolute())) for f in available_fonts())
