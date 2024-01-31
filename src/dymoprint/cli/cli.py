# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
import argparse
import logging
import webbrowser
from tempfile import NamedTemporaryFile

from PIL import Image, ImageOps

from dymoprint import __version__
from dymoprint.lib.constants import (
    AVAILABLE_BARCODES,
    DEFAULT_MARGIN_PX,
    PIXELS_PER_MM,
    USE_QR,
    e_qrcode,
)
from dymoprint.lib.dymo_labeler import DymoLabeler
from dymoprint.lib.font_config import FontConfig, FontStyle, NoFontFound
from dymoprint.lib.logger import configure_logging, set_verbose
from dymoprint.lib.render_engines import (
    BarcodeRenderEngine,
    BarcodeWithTextRenderEngine,
    HorizontallyCombinedRenderEngine,
    PictureRenderEngine,
    QrRenderEngine,
    RenderContext,
    TestPatternRenderEngine,
    TextRenderEngine,
)
from dymoprint.lib.unicode_blocks import image_to_unicode
from dymoprint.lib.utils import system_run
from dymoprint.metadata import our_metadata

LOG = logging.getLogger(__name__)

FLAG_TO_STYLE = {
    "r": FontStyle.REGULAR,
    "b": FontStyle.BOLD,
    "i": FontStyle.ITALIC,
    "n": FontStyle.NARROW,
}


class CommandLineUsageError(Exception):
    pass


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
        "--frame-width-px",
        action="count",
        help="Draw frame around the text, more arguments for thicker frame",
    )
    parser.add_argument(
        "-s",
        "--style",
        choices=["r", "b", "i", "n"],
        default="r",
        help="Set fonts style (regular,bold,italic,narrow)",
    )
    parser.add_argument(
        "-a",
        "--align",
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
        "--justify",
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
        "-u", "--font", nargs="?", help='Set user font, overrides "-s" parameter'
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
        "--margin-px",
        type=int,
        default=DEFAULT_MARGIN_PX,
        help=f"Margin in px (default is {DEFAULT_MARGIN_PX})",
    )
    parser.add_argument(
        "--scale", type=int, default=90, help="Scaling font factor, [0,10] [%%]"
    )
    parser.add_argument(
        "-t",
        "--tape-size-mm",
        type=int,
        choices=[6, 9, 12, 19],
        default=12,
        help="Tape size: 6,9,12,19 mm, default=12mm",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase logging verbosity",
    )
    return parser.parse_args()


def mm_to_payload_px(mm, margin):
    """Convert a length in mm to a number of pixels of payload.

    The print resolution is 7 pixels/mm, and margin is subtracted from each side.
    """
    return max(0, (mm * PIXELS_PER_MM) - margin * 2)


def run():
    args = parse_args()

    # read config file
    style = FLAG_TO_STYLE.get(args.style)
    try:
        font_config = FontConfig(font=args.font, style=style)
    except NoFontFound as e:
        valid_font_names = [f.stem for f in FontConfig.available_fonts()]
        msg = f"{e}. Valid fonts are: {', '.join(valid_font_names)}"
        raise CommandLineUsageError(msg) from None

    font_filename = font_config.path

    labeltext = args.text

    if args.verbose:
        set_verbose()

    # check if barcode, qrcode or text should be printed, use frames only on text
    if args.qr and not USE_QR:
        raise CommandLineUsageError(
            "QR code cannot be used without QR support " "installed"
        ) from e_qrcode

    if args.barcode and args.qr:
        raise CommandLineUsageError(
            "Can not print both QR and Barcode on the same " "label (yet)"
        )

    if args.fixed_length is not None and (
        args.min_length != 0 or args.max_length is not None
    ):
        raise CommandLineUsageError(
            "Cannot't specify min/max and fixed length at the " "same time"
        )

    if args.max_length is not None and args.max_length < args.min_length:
        raise CommandLineUsageError("Maximum length is less than minimum length")

    render_engines = []

    if args.test_pattern:
        render_engines.append(TestPatternRenderEngine(args.test_pattern))

    if args.qr:
        render_engines.append(QrRenderEngine(labeltext.pop(0)))

    elif args.barcode:
        render_engines.append(BarcodeRenderEngine(labeltext.pop(0), args.barcode))

    elif args.barcode_text:
        render_engines.append(
            BarcodeWithTextRenderEngine(
                labeltext.pop(0), args.barcode_text, font_filename, args.frame_width_px
            )
        )

    if labeltext:
        render_engines.append(
            TextRenderEngine(
                text_lines=labeltext,
                font_file_name=font_filename,
                frame_width_px=args.frame_width_px,
                font_size_ratio=int(args.scale) / 100.0,
                align=args.align,
            )
        )

    if args.picture:
        render_engines.append(PictureRenderEngine(args.picture))

    if args.fixed_length is not None:
        min_label_mm_len = args.fixed_length
        max_label_mm_len = args.fixed_length
    else:
        min_label_mm_len = args.min_length
        max_label_mm_len = args.max_length

    margin = args.margin_px
    min_payload_len_px = mm_to_payload_px(min_label_mm_len, margin)
    max_payload_len_px = (
        mm_to_payload_px(max_label_mm_len, margin)
        if max_label_mm_len is not None
        else None
    )

    render = HorizontallyCombinedRenderEngine(
        render_engines,
        min_payload_len_px=min_payload_len_px,
        max_payload_len_px=max_payload_len_px,
        justify=args.justify,
    )

    dymo_labeler = DymoLabeler(
        margin_px=args.margin_px,
        tape_size_mm=args.tape_size_mm,
    )
    render_context = RenderContext(height_px=dymo_labeler.height_px)
    bitmap = render.render(render_context)

    # print or show the label
    if args.preview or args.preview_inverted or args.imagemagick or args.browser:
        LOG.debug("Demo mode: showing label..")
        # fix size, adding print borders
        expanded_bitmap = Image.new(
            "1", (margin + bitmap.width + margin, bitmap.height)
        )
        expanded_bitmap.paste(bitmap, (margin, 0))
        if args.preview or args.preview_inverted:
            label_rotated = expanded_bitmap.transpose(Image.ROTATE_270)
            print(image_to_unicode(label_rotated, invert=args.preview_inverted))
        if args.imagemagick:
            ImageOps.invert(expanded_bitmap).show()
        if args.browser:
            with NamedTemporaryFile(suffix=".png", delete=False) as fp:
                ImageOps.invert(expanded_bitmap).save(fp)
                webbrowser.open(f"file://{fp.name}")
    else:
        dymo_labeler.print(bitmap)


def main():
    with system_run():
        configure_logging()
        run()
