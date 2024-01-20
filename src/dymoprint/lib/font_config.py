from pathlib import Path

from dymoprint._vendor.matplotlib import font_manager
from dymoprint.lib.config_file import ConfigFile
from dymoprint.lib.constants import DEFAULT_FONT_DIR, DEFAULT_FONT_STYLE, FLAG_TO_STYLE


def font_filename(flag):
    config_fonts = ConfigFile().fonts_section
    if config_fonts:
        style_to_file = config_fonts
    else:
        # Default values
        style_to_file = {
            "regular": str(DEFAULT_FONT_DIR / "Carlito-Regular.ttf"),
            "bold": str(DEFAULT_FONT_DIR / "Carlito-Bold.ttf"),
            "italic": str(DEFAULT_FONT_DIR / "Carlito-Italic.ttf"),
            "narrow": str(DEFAULT_FONT_DIR / "Carlito-BoldItalic.ttf"),
        }

    return style_to_file[FLAG_TO_STYLE.get(flag, DEFAULT_FONT_STYLE)]


def available_fonts():
    fonts = [f for f in DEFAULT_FONT_DIR.iterdir() if f.suffix == ".ttf"]
    fonts.extend(Path(f) for f in font_manager.findSystemFonts())
    return sorted(fonts, key=lambda f: f.stem.lower())


def parse_fonts():
    return ((f.stem, str(f.absolute())) for f in available_fonts())
