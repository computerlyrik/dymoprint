from __future__ import annotations

import array
import logging
import math

import usb
from PIL import Image

from dymoprint import DymoLabeler
from dymoprint.lib.constants import DEFAULT_MARGIN_PX
from dymoprint.lib.detect import DetectedDevice

LOG = logging.getLogger(__name__)


def print_label(
    detected_device: DetectedDevice,
    label_bitmap: Image.Image,
    margin_px: int = DEFAULT_MARGIN_PX,
    tape_size_mm: int = 12,
) -> None:
    """Print a label bitmap to the detected printer.

    The label bitmap is a PIL image in 1-bit format (mode=1), and pixels with value
    equal to 1 are burned.
    """
    assert detected_device is not None
    # Convert the image to the proper matrix for the dymo labeler object so that
    # rows span the width of the label, and the first row corresponds to the left
    # edge of the label.
    label_rotated = label_bitmap.transpose(Image.ROTATE_270)

    # Convert the image to raw bytes. Pixels along rows are chunked into groups of
    # 8 pixels, and subsequent rows are concatenated.
    labelstream: bytes = label_rotated.tobytes()

    # Regather the bytes into rows
    label_stream_row_length = int(math.ceil(label_bitmap.height / 8))
    if len(labelstream) // label_stream_row_length != label_bitmap.width:
        raise RuntimeError(
            "An internal problem was encountered while processing the " "label bitmap!"
        )
    label_rows: list[bytes] = [
        labelstream[i : i + label_stream_row_length]
        for i in range(0, len(labelstream), label_stream_row_length)
    ]

    # Convert bytes into ints
    label_matrix: list[list[int]] = [
        array.array("B", label_row).tolist() for label_row in label_rows
    ]

    lm = DymoLabeler(
        detected_device.devout,
        detected_device.devin,
        synwait=64,
        tape_size_mm=tape_size_mm,
    )

    LOG.debug("Printing label..")
    lm.print_label(label_matrix, margin_px=margin_px)
    LOG.debug("Done printing.")
    usb.util.dispose_resources(detected_device.dev)
    LOG.debug("Cleaned up.")
