from enum import Enum


class _RenderContextFieldName(Enum):
    BACKGROUND_COLOR = 1
    FOREGROUND_COLOR = 2
    HEIGHT_PX = 3
    PREVIEW_SHOW_MARGINS = 4


class RenderContext:
    _context: dict

    def __init__(self, **kwargs):
        self._context = dict()
        for k, v in kwargs.items():
            self._context[_RenderContextFieldName[k.upper()].name.lower()] = v

        # add property per field name (e.g. context.height_px)
        for field in _RenderContextFieldName:

            def get_fget(field=field):
                return lambda _self: _self._context[field.name.lower()]

            def get_fset(field=field):
                def fset(_self, val):
                    _self._context[field.name.lower()] = val

                return fset

            setattr(
                self.__class__,
                field.name.lower(),
                property(get_fget(field), get_fset(field)),
            )

    def __str__(self):
        return self._context.__str__()
