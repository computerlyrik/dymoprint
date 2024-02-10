from __future__ import annotations

from typing import Literal

from PIL import Image, ImageColor, ImageDraw, ImageOps

from dymoprint.lib.render_engines.margins import MarginsMode, MarginsRenderEngine
from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine
from dymoprint.lib.utils import px_to_mm


class PrintPreviewRenderEngine(RenderEngine):
    X_MARGIN_PX = 80
    Y_MARGIN_PX = 30
    DX = X_MARGIN_PX * 0.3
    DY = Y_MARGIN_PX * 0.3
    MARGIN_COLOR = "red"
    MARK_COLOR = "yellow"
    TEXT_COLOR = "blue"

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

        preview_width_mark_y = preview_height - self.Y_MARGIN_PX + self.DY
        label_width_mark_y = preview_height - self.DY
        preview_width_mark_x = self.X_MARGIN_PX - self.DX
        label_width_mark_x = self.DX

        # left vertical margin
        draw.line(
            xy=(
                self.X_MARGIN_PX + x_margin,
                0,
                self.X_MARGIN_PX + x_margin,
                preview_width_mark_y,
            ),
            fill=self.MARGIN_COLOR,
        )
        # right vertical margin
        draw.line(
            xy=(
                self.X_MARGIN_PX + label_width - x_margin,
                0,
                self.X_MARGIN_PX + label_width - x_margin,
                preview_width_mark_y,
            ),
            fill=self.MARGIN_COLOR,
        )
        # top horizontal margin
        draw.line(
            xy=(
                preview_width_mark_x,
                self.DY + y_margin,
                preview_width,
                self.DY + y_margin,
            ),
            fill=self.MARGIN_COLOR,
        )
        # bottom horizontal margin
        draw.line(
            xy=(
                preview_width_mark_x,
                self.DY + label_height - y_margin,
                preview_width,
                self.DY + label_height - y_margin,
            ),
            fill=self.MARGIN_COLOR,
        )
        # horizontal line for payload width
        draw.line(
            xy=(
                self.X_MARGIN_PX + x_margin,
                preview_width_mark_y,
                self.X_MARGIN_PX + label_width - x_margin,
                preview_width_mark_y,
            ),
            fill=self.MARK_COLOR,
        )
        # horizontal line for label width
        draw.line(
            xy=(
                self.X_MARGIN_PX,
                label_width_mark_y,
                self.X_MARGIN_PX + label_width,
                label_width_mark_y,
            ),
            fill=self.MARK_COLOR,
        )
        # vertical line for payload height
        draw.line(
            xy=(
                preview_width_mark_x,
                self.DY + y_margin,
                preview_width_mark_x,
                self.DY + label_height - y_margin,
            ),
            fill=self.MARK_COLOR,
        )
        # vertical line for label height
        draw.line(
            xy=(
                label_width_mark_x,
                self.DY,
                label_width_mark_x,
                self.DY + label_height,
            ),
            fill=self.MARK_COLOR,
        )

        labels = [
            # payload width
            {
                "xy": (self.X_MARGIN_PX + label_width / 2, preview_width_mark_y),
                "text": f"{px_to_mm(label_width - x_margin * 2)} mm",
                "anchor": "mm",
                "align": "center",
            },
            # label width
            {
                "xy": (self.X_MARGIN_PX + label_width / 2, label_width_mark_y),
                "text": f"{px_to_mm(label_width)} mm",
                "anchor": "mm",
                "align": "center",
            },
            # payload height
            {
                "xy": (preview_width_mark_x, self.DY + label_height / 2 - self.DY),
                "text": f"{px_to_mm(label_height - y_margin * 2)} mm",
                "anchor": "mm",
                "align": "center",
            },
            # label height
            {
                "xy": (label_width_mark_x, self.DY + label_height / 2 + self.DY),
                "text": f"{px_to_mm(label_height)} mm",
                "anchor": "mm",
                "align": "center",
            },
        ]
        for label in labels:
            bbox = draw.textbbox(**label)  # type: ignore[arg-type]
            draw.rectangle(bbox, fill=(0, 0, 0, 0))
            draw.text(**label, fill=self.TEXT_COLOR)  # type: ignore[arg-type]

    def render(self, context: RenderContext) -> Image.Image:
        label_bitmap, meta = self._get_label_bitmap(context)
        if context.preview_show_margins:
            label_width, label_height = label_bitmap.size
            preview_width = label_width + self.X_MARGIN_PX + self.DX
            preview_height = label_height + self.Y_MARGIN_PX + self.DY
            preview_bitmap = Image.new(
                "RGBA",
                (round(preview_width), round(preview_height)),
                color=(0, 0, 0, 0),
            )
            preview_bitmap.paste(label_bitmap, box=(self.X_MARGIN_PX, round(self.DY)))
            self._show_margins(label_bitmap, preview_bitmap, meta, context)
            return preview_bitmap
        else:
            return label_bitmap
