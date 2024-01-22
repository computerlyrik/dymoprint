# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

import contextlib
import math
import os
import sys

from PIL import ImageDraw

from dymoprint.lib.constants import PIXELS_PER_MM


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


def is_debug_mode():
    return any(env_var in os.environ for env_var in ("DEBUG", "VERBOSE"))


def print_exception(e):
    print(f"Error: {e}", file=sys.stderr)
