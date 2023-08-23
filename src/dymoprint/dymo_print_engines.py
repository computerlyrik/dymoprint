from __future__ import annotations

import array
import math
import os
import platform
from typing import NoReturn

import barcode as barcode_module
import usb
from PIL import Image, ImageFont, ImageOps

from . import DymoLabeler
from .barcode_writer import BarcodeImageWriter
from .constants import (
    DEFAULT_MARGIN,
    DEV_VENDOR,
    HID_INTERFACE_CLASS,
    PIXELS_PER_MM,
    PRINTER_INTERFACE_CLASS,
    SUPPORTED_PRODUCTS,
    UNCONFIRMED_MESSAGE,
    QRCode,
)
from .utils import die, draw_image, scaling

GITHUB_LINK = "<https://github.com/computerlyrik/dymoprint/pull/56>"


def device_info(dev: usb.core.Device) -> str:
    try:
        dev.manufacturer
    except ValueError:
        instruct_on_access_denied(dev)
    res = ""
    res += f"{repr(dev)}\n"
    res += f"  manufacturer: {dev.manufacturer}\n"
    res += f"  product: {dev.product}\n"
    res += f"  serial: {dev.serial_number}\n"
    configs = dev.configurations()
    if configs:
        res += "  configurations:\n"
        for cfg in configs:
            res += f"  - {repr(cfg)}\n"
            intfs = cfg.interfaces()
            if intfs:
                res += "    interfaces:\n"
                for intf in intfs:
                    res += f"    - {repr(intf)}\n"
    return res


def instruct_on_access_denied(dev: usb.core.Device) -> NoReturn:
    system = platform.system()
    if system == "Linux":
        instruct_on_access_denied_linux(dev)
    elif system == "Windows":
        raise RuntimeError(
            "Couldn't access the device. Please make sure that the "
            "device driver is set to WinUSB. This can be accomplished "
            "with Zadig <https://zadig.akeo.ie/>."
        )
    elif system == "Darwin":
        raise RuntimeError(
            f"Could not access {dev}. Thanks for bravely trying this on a Mac. You "
            f"are in uncharted territory. It would be appreciated if you share the "
            f"results of your experimentation at {GITHUB_LINK}."
        )
    else:
        raise RuntimeError(f"Unknown platform {system}")


def instruct_on_access_denied_linux(dev: usb.core.Device) -> NoReturn:
    # try:
    #     os_release = platform.freedesktop_os_release()
    # except OSError:
    #     os_release = {}
    # dists_with_empties = [os_release.get("ID", "")] + os_release.get(
    #     "ID_LIKE", ""
    # ).split(" ")
    # dists = [dist for dist in dists_with_empties if dist]
    # if "arch" in dists:
    #     restart_udev_command = "sudo udevadm control --reload"
    # elif "ubuntu" in dists or "debian" in dists:
    #     restart_udev_command = "sudo systemctl restart udev.service"
    # # detect whether we are in arch linux or ubuntu linux
    # if Path("/etc/arch-release").exists():
    #     restart_udev_command = "sudo udevadm control --reload"
    # elif Path("/etc/lsb-release").exists():
    #     restart_udev_command = "sudo systemctl restart udev.service"
    # else:
    #     restart_udev_command = None

    lines = []
    lines.append(
        "You do not have sufficient access to the "
        "device. You probably want to add the a udev rule in "
        "/etc/udev/rules.d with the following command:"
    )
    lines.append("")
    udev_rule = ", ".join(
        [
            'ACTION=="add"',
            'SUBSYSTEMS=="usb"',
            f'ATTRS{{idVendor}}=="{dev.idVendor:04x}"',
            f'ATTRS{{idProduct}}=="{dev.idProduct:04x}"',
            'MODE="0666"',
        ]
    )
    lines.append(
        f"  echo '{udev_rule}' "
        f"| sudo tee /etc/udev/rules.d/91-dymo-{dev.idProduct:x}.rules"
    )
    lines.append("")
    lines.append("Next refresh udev with:")
    lines.append("")
    lines.append("  sudo udevadm control --reload-rules")
    lines.append('  sudo udevadm trigger --attr-match=idVendor="0922"')
    lines.append("")
    lines.append(
        "Finally, turn your device off and back "
        "on again to activate the new permissions."
    )
    lines.append("")
    lines.append(
        f"If this still does not resolve the problem, you might need to reboot. "
        f"In case rebooting is necessary, please report this at {GITHUB_LINK}. "
        f"We are still trying to figure out a simple procedure which works "
        f"for everyone. In case you still cannot connect, "
        f"or if you have any information or ideas, please post them at "
        f"that link."
    )
    raise RuntimeError("\n\n" + "\n".join(lines) + "\n")


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
        boxes = (font.getbbox(line) for line in labeltext)
        line_widths = (right - left for left, _, right, _ in boxes)
        label_width = max(line_widths) + (font_offset * 2)
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

    def merge_render(
        self, bitmaps, min_payload_len=0, max_payload_len=None, justify="center"
    ):
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

        if max_payload_len is not None and label_bitmap.width > max_payload_len:
            excess_px = label_bitmap.width - max_payload_len
            excess_mm = excess_px / PIXELS_PER_MM
            # Round up to nearest 0.1mm
            excess_mm = math.ceil(excess_mm * 10) / 10
            die(
                f"Error: Label exceeds allowed length by "
                f"exceeds allowed length of {excess_mm:.1f} mm."
            )

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

        syn_wait = 64

        dymo_devs = list(usb.core.find(idVendor=DEV_VENDOR, find_all=True))
        if len(dymo_devs) == 0:
            print(f"No Dymo devices found (expected vendor {hex(DEV_VENDOR)})")
            for dev in usb.core.find(find_all=True):
                print(
                    f"- Vendor ID: {hex(dev.idVendor):6}  "
                    f"Product ID: {hex(dev.idProduct)}"
                )
            die("Unable to open device.")
        if len(dymo_devs) > 1:
            print("Found multiple Dymo devices:")
            for dev in dymo_devs:
                print(device_info(dev))
            print("Using first device.")
            dev = dymo_devs[0]
        else:
            dev = dymo_devs[0]
            print(f"Found one Dymo device: {device_info(dev)}")
        dev = dymo_devs[0]
        if dev.idProduct in SUPPORTED_PRODUCTS:
            print(f"Recognized device as {SUPPORTED_PRODUCTS[dev.idProduct]}")
        else:
            print(f"Unrecognized device: {hex(dev.idProduct)}. {UNCONFIRMED_MESSAGE}")

        try:
            dev.get_active_configuration()
            print("Active device configuration already found.")
        except usb.core.USBError:
            try:
                dev.set_configuration()
                print("Device configuration set.")
            except usb.core.USBError as e:
                if e.errno == 13:
                    raise RuntimeError("Access denied")
                if e.errno == 16:
                    print("Device is busy, but this is okay.")
                else:
                    raise

        intf = usb.util.find_descriptor(
            dev.get_active_configuration(), bInterfaceClass=PRINTER_INTERFACE_CLASS
        )
        if intf is not None:
            print(f"Opened printer interface: {repr(intf)}")
        else:
            intf = usb.util.find_descriptor(
                dev.get_active_configuration(), bInterfaceClass=HID_INTERFACE_CLASS
            )
            if intf is not None:
                print(f"Opened HID interface: {repr(intf)}")
            else:
                die("Could not open a valid interface.")
        assert isinstance(intf, usb.core.Interface)

        try:
            if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                print(f"Detaching kernel driver from interface {intf.bInterfaceNumber}")
                dev.detach_kernel_driver(intf.bInterfaceNumber)
        except NotImplementedError:
            print(f"Kernel driver detaching not necessary on " f"{platform.system()}.")
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
            die("The device endpoints not be found.")

        # create dymo labeler object
        lm = DymoLabeler(devout, devin, synwait=syn_wait, tape_size=tape_size)

        print("Printing label..")
        lm.printLabel(label_matrix, margin=margin)
        print("Done printing.")
        usb.util.dispose_resources(dev)
        print("Cleaned up.")
