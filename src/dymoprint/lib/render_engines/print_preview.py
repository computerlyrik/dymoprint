from __future__ import annotations

from typing import Literal

from PIL import Image, ImageColor, ImageOps

from dymoprint.lib.render_engines.margins import MarginsMode, MarginsRenderEngine
from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine


class PrintPreviewRenderEngine(RenderEngine):
    def __init__(
        self,
        render_engine: RenderEngine,
        justify: Literal["left", "center", "right"] = "center",
        visible_horizontal_margin_px: float = 0,
        labeler_margin_px: tuple[float, float] = (0, 0),
        max_width_px: float | None = None,
        min_width_px: float = 0,
    ):
        super().__init__()
        self.render_engine = MarginsRenderEngine(
            render_engine=render_engine,
            mode=MarginsMode.PREVIEW,
            justify=justify,
            visible_horizontal_margin_px=visible_horizontal_margin_px,
            labeler_margin_px=labeler_margin_px,
            max_width_px=max_width_px,
            min_width_px=min_width_px,
        )

    def _get_preview_bitmap(self, context: RenderContext):
        label_bitmap = self.render_engine.render(context)
        bitmap = ImageOps.invert(label_bitmap.convert("L")).convert("RGBA")
        pixel_map = {
            "black": context.foreground_color,
            "white": context.background_color,
        }
        pixel_color_map = {
            ImageColor.getcolor(k, "RGBA"): ImageColor.getcolor(v, "RGBA")
            for k, v in pixel_map.items()
        }
        pixdata = bitmap.load()
        width, height = bitmap.size
        for x in range(0, width):
            for y in range(0, height):
                pixdata[x, y] = pixel_color_map[pixdata[x, y]]
        return bitmap

    def render(self, context: RenderContext) -> Image.Image:
        return self._get_preview_bitmap(context)
