from __future__ import annotations

import array
import math
import os

import barcode as barcode_module
import usb
from PIL import Image, ImageFont, ImageOps

from . import DymoLabeler
from .barcode_writer import BarcodeImageWriter
from .constants import (
    DEFAULT_MARGIN,
    DEV_CLASS,
    DEV_LM280_CLASS,
    DEV_LM280_PRODUCT,
    DEV_NAME,
    DEV_NODE,
    DEV_PRODUCT,
    DEV_VENDOR,
    QRCode,
)
from .utils import access_error, die, draw_image, getDeviceFile, scaling


class DymoRenderEngine:
    def __init__(self, tape_size=12):
        """
        Initializes a DymoRenderEngine object with a specified tape size.

        Args:
            tape_size (int): The size of the tape in millimeters. Default is 12mm.
        """
        self.tape_size = tape_size

    def render_empty(self, label_len=1):
        """
        Renders an empty label image.

        Returns:
            Image: An empty label image.
        """
        label_height = DymoLabeler.max_bytes_per_line(self.tape_size) * 8
        return Image.new("1", (label_len, label_height))

    def render_qr(self, qr_input_text):
        """
        Renders a QR code image from the input text.

        Args:
            qr_input_text (str): The input text to be encoded in the QR code.

        Returns:
            Image: A QR code image.
        """
        label_height = DymoLabeler.max_bytes_per_line(self.tape_size) * 8
        if len(qr_input_text) == 0:
            return Image.new("1", (1, label_height))

        # create QR object from first string
        code = QRCode(qr_input_text, error="M")
        qr_text = code.text(quiet_zone=1).split()

        # create an empty label image
        qr_scale = label_height // len(qr_text)
        qr_offset = (label_height - len(qr_text) * qr_scale) // 2
        label_width = len(qr_text) * qr_scale

        if not qr_scale:
            die(
                "Error: too much information to store in the QR code, points "
                "are smaller than the device resolution"
            )

        code_bitmap = Image.new("1", (label_width, label_height))

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

    def render_barcode(self, barcode_input_text, bar_code_type):
        """
        Renders a barcode image from the input text and barcode type.

        Args:
            barcode_input_text (str): The input text to be encoded in the barcode.
            bar_code_type (str): The type of barcode to be rendered.

        Returns:
            Image: A barcode image.
        """
        label_height = DymoLabeler.max_bytes_per_line(self.tape_size) * 8
        if len(barcode_input_text) == 0:
            return Image.new("1", (1, label_height))

        code = barcode_module.get(
            bar_code_type, barcode_input_text, writer=BarcodeImageWriter()
        )
        code_bitmap = code.render(
            {
                "font_size": 0,
                "vertical_margin": 8,
                "module_height": (DymoLabeler.max_bytes_per_line(self.tape_size) * 8)
                - 16,
                "module_width": 2,
                "background": "black",
                "foreground": "white",
            }
        )
        return code_bitmap

    def render_text(
        self,
        labeltext: list[str],
        font_file_name: str,
        frame_width,
        font_size_ratio=0.9,
        align="left",
    ):
        """
        Renders a text image from the input text, font file name, frame width, and
        font size ratio.

        Args:
            labeltext (list[str]): The input text to be rendered.
            font_file_name (str): The name of the font file to be used.
            frame_width (int): The width of the frame around the text.
            font_size_ratio (float): The ratio of font size to line height. Default
                is 1.

        Returns:
            Image: A text image.
        """
        if type(labeltext) is str:
            labeltext = [labeltext]

        if len(labeltext) == 0:
            labeltext = [" "]

        # create an empty label image
        label_height = DymoLabeler.max_bytes_per_line(self.tape_size) * 8
        line_height = float(label_height) / len(labeltext)
        fontsize = int(round(line_height * font_size_ratio))

        font_offset = int((line_height - fontsize) / 2)

        if frame_width:
            frame_width = min(frame_width, font_offset)
            frame_width = min(frame_width, 3)

        font = ImageFont.truetype(font_file_name, fontsize)
        label_width = max(font.getsize(line)[0] for line in labeltext) + (
            font_offset * 2
        )
        text_bitmap = Image.new("1", (label_width, label_height))
        with draw_image(text_bitmap) as label_draw:
            # draw frame into empty image
            if frame_width:
                label_draw.rectangle(
                    ((0, 4), (label_width - 1, label_height - 4)), fill=255
                )
                label_draw.rectangle(
                    (
                        (frame_width, 4 + frame_width),
                        (
                            label_width - (frame_width + 1),
                            label_height - (frame_width + 4),
                        ),
                    ),
                    fill=0,
                )

            # write the text into the empty image
            multiline_text = "\n".join(labeltext)
            label_draw.multiline_text(
                (label_width / 2, label_height / 2),
                multiline_text,
                align=align,
                anchor="mm",
                font=font,
                fill=255,
            )
        return text_bitmap

    def render_picture(self, picture_path: str):
        """
        Renders a picture image from the input picture path.

        Args:
            picture_path (str): The path of the picture to be rendered.

        Returns:
            Image: A picture image.
        """
        if len(picture_path):
            if os.path.exists(picture_path):
                label_height = DymoLabeler.max_bytes_per_line(self.tape_size) * 8
                with Image.open(picture_path) as img:
                    if img.height > label_height:
                        ratio = label_height / img.height
                        img = img.resize(
                            (int(math.ceil(img.width * ratio)), label_height)
                        )

                    img = img.convert("L", palette=Image.AFFINE)
                    return ImageOps.invert(img).convert("1")
            else:
                die(f"picture path:{picture_path}  doesn't exist ")
        label_height = DymoLabeler.max_bytes_per_line(self.tape_size) * 8
        return Image.new("1", (1, label_height))

    def merge_render(self, bitmaps, min_payload_len=0, justify="center"):
        """
        Merges multiple images into a single image.

        Args:
            bitmaps (list[Image]): A list of images to be merged.

        Returns:
            Image: A merged image.
        """
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
            label_bitmap = self.render_empty(max(min_payload_len, 1))
        else:
            label_bitmap = bitmaps[0]

        if min_payload_len > label_bitmap.width:
            offset = 0
            if justify == "center":
                offset = max(0, int((min_payload_len - label_bitmap.width) / 2))
            if justify == "right":
                offset = max(0, int(min_payload_len - label_bitmap.width))
            out_label_bitmap = Image.new(
                "1",
                (
                    min_payload_len,
                    label_bitmap.height,
                ),
            )
            out_label_bitmap.paste(label_bitmap, box=(offset, 0))
            return out_label_bitmap

        return label_bitmap


class DymoPrinterServer:
    @staticmethod
    def print_label(label_bitmap, margin=DEFAULT_MARGIN, tape_size: int = 12):
        """
        Prints a label using a Dymo labeler object.

        :param label_bitmap: The image to be printed as a label.
        :type label_bitmap: Image
        :param margin: The margin size in dots.
        :type margin: int, optional
        :param tape_size: The size of the tape in millimeters. Default is 12.
        :type tape_size: int, optional
        :return: None
        :rtype: None
        """
        # convert the image to the proper matrix for the dymo labeler object
        label_rotated = label_bitmap.transpose(Image.ROTATE_270)
        labelstream = label_rotated.tobytes()
        label_stream_row_length = int(math.ceil(label_bitmap.height / 8))
        if len(labelstream) // label_stream_row_length != label_bitmap.width:
            die(
                "An internal problem was encountered while processing the label "
                "bitmap!"
            )
        label_rows = [
            labelstream[i : i + label_stream_row_length]
            for i in range(0, len(labelstream), label_stream_row_length)
        ]
        label_matrix = [
            array.array("B", label_row).tolist() for label_row in label_rows
        ]
        # get device file name
        if not DEV_NODE:
            dev = getDeviceFile(DEV_CLASS, DEV_VENDOR, DEV_PRODUCT)
        else:
            dev = DEV_NODE

        if dev:
            try:
                devout = open(dev, "rb+")
            except PermissionError:
                access_error(dev)
            devin = devout
            # We are in the normal HID file mode, so no syn_wait is needed.
            syn_wait = None
            in_usb_mode = False
        else:
            # We are in the experimental PyUSB mode, if a device can be found.
            syn_wait = 64
            # Find and prepare device communication endpoints.
            dev = usb.core.find(
                custom_match=lambda d: (
                    d.idVendor == DEV_VENDOR and d.idProduct == DEV_LM280_PRODUCT
                )
            )

            if dev is None:
                die("The device '%s' could not be found on this system." % DEV_NAME)
            else:
                print("Entering experimental PyUSB mode.")
                in_usb_mode = True

            try:
                dev.set_configuration()
            except usb.core.USBError as e:
                if e.errno == 13:
                    raise RuntimeError("Access denied")
                if e.errno == 16:
                    # Resource busy
                    pass
                else:
                    raise

            intf = usb.util.find_descriptor(
                dev.get_active_configuration(), bInterfaceClass=DEV_LM280_CLASS
            )
            if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                dev.detach_kernel_driver(intf.bInterfaceNumber)
            devout = usb.util.find_descriptor(
                intf,
                custom_match=(
                    lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                    == usb.util.ENDPOINT_OUT
                ),
            )
            devin = usb.util.find_descriptor(
                intf,
                custom_match=(
                    lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                    == usb.util.ENDPOINT_IN
                ),
            )

        if not devout or not devin:
            die("The device '%s' could not be found on this system." % DEV_NAME)

        # create dymo labeler object
        try:
            lm = DymoLabeler(devout, devin, synwait=syn_wait, tape_size=tape_size)
        except OSError:
            access_error(dev)

        print("Printing label..")
        lm.printLabel(label_matrix, margin=margin)
        print("Done printing.")

        if in_usb_mode:
            usb.util.dispose_resources(dev)
