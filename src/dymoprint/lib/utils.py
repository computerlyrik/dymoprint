# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

import contextlib
import logging
import math

from PIL import ImageDraw

from dymoprint.lib.constants import PIXELS_PER_MM

LOG = logging.getLogger(__name__)


def scaling(pix, sc):
    """Scaling pixel up, input: (x,y),scale-factor."""
    return [(pix[0] + i, pix[1] + j) for i in range(sc) for j in range(sc)]


@contextlib.contextmanager
def draw_image(bitmap):
    drawobj = ImageDraw.Draw(bitmap)
    assert isinstance(drawobj, ImageDraw.ImageDraw)
    try:
        yield drawobj
    finally:
        del drawobj


def px_to_mm(px):
    mm = px / PIXELS_PER_MM
    # Round up to nearest 0.1mm
    return math.ceil(mm * 10) / 10
