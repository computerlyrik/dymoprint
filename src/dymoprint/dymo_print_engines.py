from __future__ import annotations

import array
import math
from pathlib import Path

import barcode as barcode_module
import usb
from PIL import Image, ImageFont, ImageOps

from . import DymoLabeler
from .barcode_writer import BarcodeImageWriter
from .constants import DEFAULT_MARGIN_PX, PIXELS_PER_MM, QRCode
from .detect import DetectedDevice
from .utils import die, draw_image, scaling


class DymoRenderEngine:
    label_height_px: int

    def __init__(self, tape_size_mm: int = 12) -> None:
        """Initialize a DymoRenderEngine object with a specified tape size."""
        self.label_height_px = DymoLabeler.max_bytes_per_line(tape_size_mm) * 8

    def render_empty(self, label_len: int = 1) -> Image.Image:
        """Render an empty label image."""
        return Image.new("1", (label_len, self.label_height_px))

    def render_test(self, width: int = 100) -> Image.Image:
        """Render a test pattern"""
        canvas = Image.new("1", (10 + width + 2 + 40, width))

        # 5 vertical lines
        for x in range(0, 9, 2):
            for y in range(canvas.height):
                canvas.putpixel((x, y), 1)

        # checkerboard pattern
        cb = Image.new("1", (width, width))
        ss = 1
        while ss <= (width / 2):
            for x in range(ss - 1, 2 * ss - 1):
                for y in range(0, width):
                    if (math.floor(y / ss) % 2) == 0:
                        cb.putpixel((x, y), 1)
            ss *= 2
        canvas.paste(cb, (10, 0))

        # a bunch of horizontal lines, on top and bottom
        hl = Image.new("1", (20, 9))
        for y in range(0, 9, 2):
            for x in range(20):
                hl.putpixel((x, y), 1)
        canvas.paste(hl, (10 + width + 2, 0))
        canvas.paste(hl, (10 + width + 2, width - 9))
        canvas.paste(hl, (10 + width + 2 + 20, 1))
        canvas.paste(hl, (10 + width + 2 + 20, width - 9 - 1))

        return canvas

    def render_qr(self, qr_input_text: str) -> Image.Image:
        """Render a QR code image from the input text."""
        if len(qr_input_text) == 0:
            return Image.new("1", (1, self.label_height_px))

        # create QR object from first string
        code = QRCode(qr_input_text, error="M")
        qr_text = code.text(quiet_zone=1).split()

        # create an empty label image
        qr_scale = self.label_height_px // len(qr_text)
        qr_offset = (self.label_height_px - len(qr_text) * qr_scale) // 2
        label_width = len(qr_text) * qr_scale

        if not qr_scale:
            die(
                "Error: too much information to store in the QR code, points "
                "are smaller than the device resolution"
            )

        code_bitmap = Image.new("1", (label_width, self.label_height_px))

        with draw_image(code_bitmap) as label_draw:
            # write the qr-code into the empty image
            for i, line in enumerate(qr_text):
                for j in range(len(line)):
                    if line[j] == "1":
                        pix = scaling(
                            (j * qr_scale, i * qr_scale + qr_offset), qr_scale
                        )
                        label_draw.point(pix, 255)
        return code_bitmap

    def render_barcode(
        self, barcode_input_text: str, bar_code_type: str
    ) -> Image.Image:
        """Render a barcode image from the input text and barcode type."""
        if len(barcode_input_text) == 0:
            return Image.new("1", (1, self.label_height_px))

        code = barcode_module.get(
            bar_code_type, barcode_input_text, writer=BarcodeImageWriter()
        )
        code_bitmap = code.render(
            {
                "font_size": 0,
                "vertical_margin": 8,
                "module_height": self.label_height_px - 16,
                "module_width": 2,
                "background": "black",
                "foreground": "white",
            }
        )
        return code_bitmap

    def render_barcode_with_text(
        self,
        barcode_input_text,
        bar_code_type,
        font_file_name: str,
        frame_width,
        font_size_ratio=0.9,
        align="center",
    ):
        """
        Renders a barcode image with the text below it.

        Args:
            barcode_input_text (str): The input text to be encoded in the barcode.
            bar_code_type (str): The type of barcode to be rendered.
            font_file_name (str): The name of the font file to be used.
            frame_width (int): The width of the frame around the text.
            font_size_ratio (float): The ratio of font size to line height. Default
                is 1.

        Returns:
            Image: A barcode with text image.
        """
        assert align in ("left", "center", "right")
        # Generate barcode
        code_bitmap = self.render_barcode(barcode_input_text, bar_code_type)

        # Generate text
        text_bitmap = self.render_text(
            text_lines=barcode_input_text,
            font_file_name=font_file_name,
            frame_width_px=frame_width,
            font_size_ratio=font_size_ratio,
            align=align,
            label_height_px=code_bitmap.height // 3,
        )

        # Define the x and y of the upper-left corner of the text
        # to be pasted onto the barcode
        text_x = code_bitmap.height - text_bitmap.height - 1
        if align == "left":
            text_y = 0
        elif align == "center":
            text_y = code_bitmap.width // 2 - text_bitmap.width // 2
        elif align == "right":
            text_y = code_bitmap.width - text_bitmap.width
        else:
            raise ValueError(f"Invalid align value: {align}")

        code_bitmap.paste(text_bitmap, (text_y, text_x))
        return code_bitmap

    def render_text(
        self,
        text_lines: str | list[str],
        font_file_name: str,
        frame_width_px: int,
        font_size_ratio: float = 0.9,
        align: str = "left",
        label_height_px: int | None = None,
    ) -> Image.Image:
        """Render text to image.

        font_size_ratio is the ratio of font size to line height.
        """
        assert align in ("left", "center", "right")
        if isinstance(text_lines, str):
            text_lines = [text_lines]

        if len(text_lines) == 0:
            text_lines = [" "]

        # create an empty label image
        if label_height_px is None:
            label_height_px = self.label_height_px
        line_height = float(label_height_px) / len(text_lines)
        font_size_px = int(round(line_height * font_size_ratio))

        font_offset_px = int((line_height - font_size_px) / 2)

        if frame_width_px:
            frame_width_px = min(frame_width_px, font_offset_px)
            frame_width_px = min(frame_width_px, 3)

        font = ImageFont.truetype(font_file_name, font_size_px)
        boxes = (font.getbbox(line) for line in text_lines)
        line_widths = (right - left for left, _, right, _ in boxes)
        label_width_px = max(line_widths) + (font_offset_px * 2)
        text_bitmap = Image.new("1", (label_width_px, label_height_px))
        with draw_image(text_bitmap) as label_draw:
            # draw frame into empty image
            if frame_width_px:
                label_draw.rectangle(
                    ((0, 4), (label_width_px - 1, label_height_px - 4)), fill=1
                )
                label_draw.rectangle(
                    (
                        (frame_width_px, 4 + frame_width_px),
                        (
                            label_width_px - (frame_width_px + 1),
                            label_height_px - (frame_width_px + 4),
                        ),
                    ),
                    fill=0,
                )

            # write the text into the empty image
            multiline_text = "\n".join(text_lines)
            label_draw.multiline_text(
                (label_width_px / 2, label_height_px / 2),
                multiline_text,
                align=align,
                anchor="mm",
                font=font,
                fill=1,
            )
        return text_bitmap

    def render_picture(self, picture_path: str) -> Image.Image:
        if len(picture_path):
            if Path(picture_path).exists():
                with Image.open(picture_path) as img:
                    if img.height > self.label_height_px:
                        ratio = self.label_height_px / img.height
                        img = img.resize(
                            (int(math.ceil(img.width * ratio)), self.label_height_px)
                        )

                    img = img.convert("L", palette=Image.AFFINE)
                    return ImageOps.invert(img).convert("1")
            else:
                die(f"picture path:{picture_path}  doesn't exist ")
        return Image.new("1", (1, self.label_height_px))

    def merge_render(
        self,
        *,
        bitmaps: list[Image.Image],
        min_payload_len_px=0,
        max_payload_len_px=None,
        justify="center",
    ) -> Image.Image:
        """Merge multiple images into a single image."""
        if len(bitmaps) > 1:
            padding = 4
            label_bitmap = Image.new(
                "1",
                (
                    sum(b.width for b in bitmaps) + padding * (len(bitmaps) - 1),
                    bitmaps[0].height,
                ),
            )
            offset = 0
            for bitmap in bitmaps:
                label_bitmap.paste(bitmap, box=(offset, 0))
                offset += bitmap.width + padding
        elif len(bitmaps) == 0:
            label_bitmap = self.render_empty(max(min_payload_len_px, 1))
        else:
            label_bitmap = bitmaps[0]

        if max_payload_len_px is not None and label_bitmap.width > max_payload_len_px:
            excess_px = label_bitmap.width - max_payload_len_px
            excess_mm = excess_px / PIXELS_PER_MM
            # Round up to nearest 0.1mm
            excess_mm = math.ceil(excess_mm * 10) / 10
            die(
                f"Error: Label exceeds allowed length by "
                f"exceeds allowed length of {excess_mm:.1f} mm."
            )

        if min_payload_len_px > label_bitmap.width:
            offset = 0
            if justify == "center":
                offset = max(0, int((min_payload_len_px - label_bitmap.width) / 2))
            if justify == "right":
                offset = max(0, int(min_payload_len_px - label_bitmap.width))
            out_label_bitmap = Image.new(
                "1",
                (
                    min_payload_len_px,
                    label_bitmap.height,
                ),
            )
            out_label_bitmap.paste(label_bitmap, box=(offset, 0))
            return out_label_bitmap

        return label_bitmap


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
        die("An internal problem was encountered while processing the label " "bitmap!")
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

    print("Printing label..")
    lm.printLabel(label_matrix, margin_px=margin_px)
    print("Done printing.")
    usb.util.dispose_resources(detected_device.dev)
    print("Cleaned up.")
