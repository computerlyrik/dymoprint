# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

import argparse
import os

from PIL import Image, ImageOps

from . import __version__
from .constants import DEFAULT_MARGIN, USE_QR, e_qrcode
from .dymo_print_engines import DymoPrinterServer, DymoRenderEngine
from .font_config import font_filename
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
        "-l", type=int, default=0, help="Specify minimum label length in mm"
    )
    parser.add_argument(
        "-j",
        choices=[
            "left",
            "center",
            "right",
        ],
        default="center",
        help=(
            "Justify content of label if minimum label length "
            "is specified (left,center,right)"
        ),
    )
    parser.add_argument("-u", nargs="?", help='Set user font, overrides "-s" parameter')
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
        "-qr", action="store_true", help="Printing the first text parameter as QR-code"
    )
    parser.add_argument(
        "-c",
        choices=[
            "code39",
            "code128",
            "ean",
            "ean13",
            "ean8",
            "gs1",
            "gtin",
            "isbn",
            "isbn10",
            "isbn13",
            "issn",
            "jan",
            "pzn",
            "upc",
            "upca",
        ],
        default=False,
        help="Printing the first text parameter as barcode",
    )
    parser.add_argument("-p", "--picture", help="Print the specified picture")
    parser.add_argument(
        "-m",
        type=int,
        default=DEFAULT_MARGIN,
        help=f"Override margin (default is {DEFAULT_MARGIN})",
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


def main():
    args = parse_args()
    print_server = DymoPrinterServer()
    render_engine = DymoRenderEngine(args.t)

    # read config file
    FONT_FILENAME = font_filename(args.s)

    labeltext = args.text

    if args.u is not None:
        if os.path.isfile(args.u):
            FONT_FILENAME = args.u
        else:
            die("Error: file '%s' not found." % args.u)

    # check if barcode, qrcode or text should be printed, use frames only on text
    if args.qr and not USE_QR:
        die("Error: %s" % e_qrcode)

    if args.c and args.qr:
        die("Error: can not print both QR and Barcode on the same label (yet)")

    bitmaps = []

    if args.qr:
        bitmaps.append(render_engine.render_qr(labeltext.pop(0)))

    elif args.c:
        bitmaps.append(render_engine.render_barcode(labeltext.pop(0), args.c))

    if labeltext:
        bitmaps.append(
            render_engine.render_text(
                labeltext, FONT_FILENAME, args.f, int(args.scale) / 100.0, args.a
            )
        )

    if args.picture:
        bitmaps.append(render_engine.render_picture(args.picture))

    margin = args.m
    justify = args.j
    min_label_mm_len: int = args.l
    min_payload_len = max(0, (min_label_mm_len * 7) - margin * 2)
    label_bitmap = render_engine.merge_render(bitmaps, min_payload_len, justify)

    # print or show the label
    if args.preview or args.preview_inverted or args.imagemagick:
        print("Demo mode: showing label..")
        # fix size, adding print borders
        label_image = Image.new(
            "L", (margin + label_bitmap.width + margin, label_bitmap.height)
        )
        label_image.paste(label_bitmap, (margin, 0))
        if args.preview or args.preview_inverted:
            label_rotated = label_bitmap.transpose(Image.ROTATE_270)
            print(image_to_unicode(label_rotated, invert=args.preview_inverted))
        if args.imagemagick:
            ImageOps.invert(label_image).show()
    else:
        print_server.print_label(label_bitmap, margin=args.m, tape_size=args.t)
