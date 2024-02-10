from enum import Enum
from pathlib import Path
from typing import Optional

import dymoprint.resources.fonts
from dymoprint._vendor.matplotlib import font_manager
from dymoprint.lib.config_file import get_config_section


class NoFontFound(ValueError):
    def __init__(self, name):
        msg = f"No font named {name} found"
        super().__init__(msg)


class FontStyle(Enum):
    REGULAR = 1
    BOLD = 2
    ITALIC = 3
    NARROW = 4

    @classmethod
    def from_name(cls, name):
        return {
            "regular": cls.REGULAR,
            "bold": cls.BOLD,
            "italic": cls.ITALIC,
            "narrow": cls.NARROW,
        }.get(name)


_DEFAULT_FONTS_DIR = Path(dymoprint.resources.fonts.__file__).parent
_DEFAULT_FONT_FILENAME = {
    FontStyle.REGULAR: str(_DEFAULT_FONTS_DIR / "Carlito-Regular.ttf"),
    FontStyle.BOLD: str(_DEFAULT_FONTS_DIR / "Carlito-Bold.ttf"),
    FontStyle.ITALIC: str(_DEFAULT_FONTS_DIR / "Carlito-Italic.ttf"),
    FontStyle.NARROW: str(_DEFAULT_FONTS_DIR / "Carlito-BoldItalic.ttf"),
}


class FontConfig:
    _DEFAULT_STYLE = FontStyle.REGULAR

    path = None

    def __init__(self, font: Optional[str] = None, style: FontStyle = _DEFAULT_STYLE):
        if font is None:
            fonts_config = get_config_section("FONTS")
            if fonts_config is not None:
                style_to_font_path = {
                    FontStyle.from_name(k): v for k, v in fonts_config.items()
                }
            else:
                style_to_font_path = _DEFAULT_FONT_FILENAME
            self.path = style_to_font_path[style]
        else:
            if Path(font).is_file():
                self.path = font
            else:
                self.path = self._path_from_name(name=font)
        assert Path(self.path).is_file()

    @classmethod
    def _path_from_name(cls, name):
        available_fonts = cls.available_fonts()
        matching_fonts = [f for f in available_fonts if name.lower() == f.stem.lower()]
        if len(matching_fonts) == 0:
            raise NoFontFound(name)
        return matching_fonts[0]

    @classmethod
    def available_fonts(cls):
        fonts = [f for f in _DEFAULT_FONTS_DIR.iterdir() if f.suffix == ".ttf"]
        fonts.extend(Path(f) for f in font_manager.findSystemFonts())
        return sorted(fonts, key=lambda f: f.stem.lower())
