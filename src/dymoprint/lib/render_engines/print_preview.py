from __future__ import annotations

from typing import Literal

from PIL import Image, ImageColor, ImageDraw, ImageOps

from dymoprint.lib.render_engines.margins import MarginsMode, MarginsRenderEngine
from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine


class PrintPreviewRenderEngine(RenderEngine):
    X_MARGIN_PX = 30
    Y_MARGIN_PX = 30
    DX = X_MARGIN_PX * 0.3
    DY = Y_MARGIN_PX * 0.3

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

    def _get_label_bitmap(self, context: RenderContext):
        render_bitmap, meta = self.render_engine.render(context)
        bitmap = ImageOps.invert(render_bitmap.convert("L")).convert("RGBA")
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
        return bitmap, meta

    def _show_margins(self, label_bitmap, preview_bitmap, meta, context):
        draw = ImageDraw.Draw(preview_bitmap)
        x_margin = meta["horizontal_offset_px"]
        y_margin = meta["vertical_offset_px"]
        preview_width, preview_height = preview_bitmap.size
        label_width, label_height = label_bitmap.size
        margin_color = context.foreground_color

        # left vertical margin
        draw.line(
            xy=(
                self.X_MARGIN_PX + x_margin,
                0,
                self.X_MARGIN_PX + x_margin,
                preview_height,
            ),
            fill=margin_color,
        )
        # right vertical margin
        draw.line(
            xy=(
                self.X_MARGIN_PX + label_width - x_margin,
                0,
                self.X_MARGIN_PX + label_width - x_margin,
                preview_height,
            ),
            fill=margin_color,
        )
        # top horizontal margin
        (
            draw.line(
                xy=(
                    0,
                    self.Y_MARGIN_PX + y_margin,
                    preview_width,
                    self.Y_MARGIN_PX + y_margin,
                ),
                fill=margin_color,
            ),
        )
        # bottom horizontal margin
        (
            draw.line(
                xy=(
                    0,
                    self.Y_MARGIN_PX + label_height - y_margin,
                    preview_width,
                    self.Y_MARGIN_PX + label_height - y_margin,
                ),
                fill=margin_color,
            ),
        )

    def render(self, context: RenderContext) -> Image.Image:
        label_bitmap, meta = self._get_label_bitmap(context)
        if context.preview_show_margins:
            label_width, label_height = label_bitmap.size
            preview_width = label_width + self.X_MARGIN_PX * 2
            preview_height = label_height + self.Y_MARGIN_PX * 2
            preview_bitmap = Image.new(
                "RGBA", (preview_width, preview_height), color=(255, 0, 0, 0)
            )
            preview_bitmap.paste(label_bitmap, box=(self.X_MARGIN_PX, self.Y_MARGIN_PX))
            self._show_margins(label_bitmap, preview_bitmap, meta, context)
            return preview_bitmap
        else:
            return label_bitmap
