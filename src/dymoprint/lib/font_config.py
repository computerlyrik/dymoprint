from enum import Enum
from pathlib import Path
from typing import Optional

import dymoprint.resources.fonts
from dymoprint._vendor.matplotlib import font_manager
from dymoprint.lib.config_file import ConfigFile


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
            if fonts_section := ConfigFile().fonts_section:
                style_to_font_path = {
                    FontStyle.from_name(k): v for k, v in fonts_section.items()
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
        try:
            return next(f.absolute() for f in cls.available_fonts() if name == f.stem)
        except StopIteration:
            raise NoFontFound(name) from None

    @classmethod
    def available_fonts(cls):
        fonts = [f for f in _DEFAULT_FONTS_DIR.iterdir() if f.suffix == ".ttf"]
        fonts.extend(Path(f) for f in font_manager.findSystemFonts())
        return sorted(fonts, key=lambda f: f.stem.lower())
