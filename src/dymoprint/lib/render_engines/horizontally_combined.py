from __future__ import annotations

from PIL import Image

from dymoprint.lib.render_engines.empty import EmptyRenderEngine
from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine


class BitmapTooBigError(ValueError):
    def __init__(self, width_px, max_width_px):
        msg = f"width_px: {width_px}, max_width_px: {max_width_px}"
        super().__init__(msg)


class HorizontallyCombinedRenderEngine(RenderEngine):
    PADDING = 4

    def __init__(
        self,
        render_engines: list[RenderEngine],
        min_payload_len_px: int = 0,
        max_payload_len_px: int | None = None,
        justify: str = "center",
    ):
        super().__init__()
        self.render_engines = render_engines
        self.min_payload_len_px = min_payload_len_px
        self.max_payload_len_px = max_payload_len_px
        self.justify = justify

    def render(self, context: RenderContext) -> Image.Image:
        render_engines = self.render_engines or [EmptyRenderEngine()]
        bitmaps = [engine.render(context) for engine in render_engines]

        if len(bitmaps) == 1:
            merged_bitmap = bitmaps[0]
        else:
            label_height = max(b.height for b in bitmaps)
            merged_bitmap = Image.new(
                "1",
                (
                    sum(b.width for b in bitmaps) + self.PADDING * (len(bitmaps) - 1),
                    label_height,
                ),
            )
            x_offset = 0
            for bitmap in bitmaps:
                y_offset = (label_height - bitmap.size[1]) // 2
                merged_bitmap.paste(bitmap, box=(x_offset, y_offset))
                x_offset += bitmap.width + self.PADDING

        if (
            self.max_payload_len_px is not None
            and merged_bitmap.width > self.max_payload_len_px
        ):
            raise BitmapTooBigError(merged_bitmap.width, self.max_payload_len_px)

        if self.min_payload_len_px > merged_bitmap.width:
            offset = 0
            if self.justify == "center":
                offset = max(
                    0, int((self.min_payload_len_px - merged_bitmap.width) / 2)
                )
            if self.justify == "right":
                offset = max(0, int(self.min_payload_len_px - merged_bitmap.width))
            expanded_merged_bitmap = Image.new(
                "1",
                (
                    self.min_payload_len_px,
                    merged_bitmap.height,
                ),
            )
            expanded_merged_bitmap.paste(merged_bitmap, box=(offset, 0))
            return expanded_merged_bitmap

        return merged_bitmap
