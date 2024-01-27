from PIL import Image

from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine


class EmptyRenderEngine(RenderEngine):
    def __init__(self, width_px: int = 1):
        super().__init__()
        self.width_px = width_px

    def render(self, context: RenderContext) -> Image.Image:
        return Image.new("1", (self.width_px, context.height_px))
