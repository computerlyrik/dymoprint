# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

import argparse
import webbrowser
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image, ImageOps

from . import __version__
from .constants import (
    AVAILABLE_BARCODES,
    DEFAULT_MARGIN_PX,
    PIXELS_PER_MM,
    USE_QR,
    e_qrcode,
)
from .detect import detect_device
from .dymo_print_engines import DymoRenderEngine, print_label
from .font_config import font_filename, available_fonts
from .metadata import our_metadata
from .unicode_blocks import image_to_unicode
from .utils import die


def parse_args():
    # check for any text specified on the command line
    parser = argparse.ArgumentParser(description=our_metadata["Summary"])
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "text",
        nargs="+",
        help="Text Parameter, each parameter gives a new line",
        type=str,
    )
    parser.add_argument(
        "-f",
        action="count",
        help="Draw frame around the text, more arguments for thicker frame",
    )
    parser.add_argument(
        "-s",
        choices=["r", "b", "i", "n"],
        default="r",
        help="Set fonts style (regular,bold,italic,narrow)",
    )
    parser.add_argument(
        "-a",
        choices=[
            "left",
            "center",
            "right",
        ],
        default="left",
        help="Align multiline text (left,center,right)",
    )
    parser.add_argument(
        "--test-pattern",
        type=int,
        default=0,
        help="Prints test pattern of a desired dot width",
    )

    length_options = parser.add_argument_group("Length options")

    length_options.add_argument(
        "-l",
        "--min-length",
        type=int,
        default=0,
        help="Specify minimum label length in mm",
    )
    length_options.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Specify maximum label length in mm, error if the label won't fit",
    )
    length_options.add_argument(
        "--fixed-length",
        type=int,
        default=None,
        help="Specify fixed label length in mm, error if the label won't fit",
    )

    length_options.add_argument(
        "-j",
        choices=[
            "left",
            "center",
            "right",
        ],
        default="center",
        help=(
            "Justify content of label if label content is less than the "
            "minimum or fixed length (left, center, right)"
        ),
    )
    parser.add_argument(
        "-u",
        "--font",
        nargs="?",
        help='Set user font, overrides "-s" parameter'
    )
    parser.add_argument(
        "-n",
        "--preview",
        action="store_true",
        help="Unicode preview of label, do not send to printer",
    )
    parser.add_argument(
        "--preview-inverted",
        action="store_true",
        help="Unicode preview of label, colors inverted, do not send to printer",
    )
    parser.add_argument(
        "--imagemagick",
        action="store_true",
        help="Preview label with Imagemagick, do not send to printer",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Preview label in the browser, do not send to printer",
    )
    parser.add_argument(
        "-qr", action="store_true", help="Printing the first text parameter as QR-code"
    )
    parser.add_argument(
        "-c",
        "--barcode",
        choices=AVAILABLE_BARCODES,
        default=False,
        help="Printing the first text parameter as barcode",
    )
    parser.add_argument(
        "--barcode-text",
        choices=AVAILABLE_BARCODES,
        default=False,
        help="Printing the first text parameter as barcode and text under it",
    )
    parser.add_argument("-p", "--picture", help="Print the specified picture")
    parser.add_argument(
        "-m",
        type=int,
        default=DEFAULT_MARGIN_PX,
        help=f"Margin in px (default is {DEFAULT_MARGIN_PX})",
    )
    parser.add_argument(
        "--scale", type=int, default=90, help="Scaling font factor, [0,10] [%%]"
    )
    parser.add_argument(
        "-t",
        type=int,
        choices=[6, 9, 12, 19],
        default=12,
        help="Tape size: 6,9,12,19 mm, default=12mm",
    )
    return parser.parse_args()


def mm_to_payload_px(mm, margin):
    """Convert a length in mm to a number of pixels of payload

    The print resolution is 7 pixels/mm, and margin is subtracted
    from each side."""
    return (mm * PIXELS_PER_MM) - margin * 2


def main():
    args = parse_args()
    render_engine = DymoRenderEngine(args.t)

    # read config file
    FONT_FILENAME = font_filename(args.s)

    labeltext = args.text

    if args.font is not None:
        if Path(args.font).is_file():
            FONT_FILENAME = args.font
        else:
            try:
                FONT_FILENAME = next(f.absolute() for f in available_fonts() if args.font == f.stem)
            except StopIteration:
                fonts = ','.join(f.stem for f in available_fonts())
                die(f"Error: file '{args.font}' not found. Available fonts: {fonts}")

    # check if barcode, qrcode or text should be printed, use frames only on text
    if args.qr and not USE_QR:
        die(f"Error: {e_qrcode}")

    if args.barcode and args.qr:
        die("Error: can not print both QR and Barcode on the same label (yet)")

    if args.fixed_length is not None and (
        args.min_length != 0 or args.max_length is not None
    ):
        die("Error: can't specify min/max and fixed length at the same time")

    if args.max_length is not None and args.max_length < args.min_length:
        die("Error: maximum length is less than minimum length")

    bitmaps = []

    if args.test_pattern:
        bitmaps.append(render_engine.render_test(args.test_pattern))

    if args.qr:
        bitmaps.append(render_engine.render_qr(labeltext.pop(0)))

    elif args.barcode:
        bitmaps.append(render_engine.render_barcode(labeltext.pop(0), args.barcode))

    elif args.barcode_text:
        bitmaps.append(
            render_engine.render_barcode_with_text(
                labeltext.pop(0), args.barcode_text, FONT_FILENAME, args.f
            )
        )

    if labeltext:
        bitmaps.append(
            render_engine.render_text(
                text_lines=labeltext,
                font_file_name=FONT_FILENAME,
                frame_width_px=args.f,
                font_size_ratio=int(args.scale) / 100.0,
                align=args.a,
            )
        )

    if args.picture:
        bitmaps.append(render_engine.render_picture(args.picture))

    margin = args.m
    justify = args.j

    if args.fixed_length is not None:
        min_label_mm_len = args.fixed_length
        max_label_mm_len = args.fixed_length
    else:
        min_label_mm_len = args.min_length
        max_label_mm_len = args.max_length

    min_payload_len_px = max(0, mm_to_payload_px(min_label_mm_len, margin))
    max_payload_len_px = (
        mm_to_payload_px(max_label_mm_len, margin)
        if max_label_mm_len is not None
        else None
    )

    label_bitmap = render_engine.merge_render(
        bitmaps=bitmaps,
        min_payload_len_px=min_payload_len_px,
        max_payload_len_px=max_payload_len_px,
        justify=justify,
    )

    # print or show the label
    if args.preview or args.preview_inverted or args.imagemagick or args.browser:
        print("Demo mode: showing label..")
        # fix size, adding print borders
        label_image = Image.new(
            "1", (margin + label_bitmap.width + margin, label_bitmap.height)
        )
        label_image.paste(label_bitmap, (margin, 0))
        if args.preview or args.preview_inverted:
            label_rotated = label_bitmap.transpose(Image.ROTATE_270)
            print(image_to_unicode(label_rotated, invert=args.preview_inverted))
        if args.imagemagick:
            ImageOps.invert(label_image).show()
        if args.browser:
            with NamedTemporaryFile(suffix='.png', delete=False) as fp:
                ImageOps.invert(label_image).save(fp)
                webbrowser.open(f'file://{fp.name}')

    else:
        detected_device = detect_device()
        print_label(detected_device, label_bitmap, margin_px=args.m, tape_size_mm=args.t)
