from __future__ import annotations

from typing import Literal

from PIL import Image, ImageOps

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

    def render(self, context: RenderContext) -> Image.Image:
        label_bitmap = self.render_engine.render(context)
        return ImageOps.invert(label_bitmap.convert("L"))
