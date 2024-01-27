from abc import ABC, abstractmethod

from PIL import Image

from dymoprint.lib.render_engines.render_context import RenderContext


class RenderEngineException(Exception):
    pass


class RenderEngine(ABC):
    @abstractmethod
    def render(self, context: RenderContext) -> Image.Image:
        pass
