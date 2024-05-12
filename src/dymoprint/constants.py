# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

# On systems with access to sysfs under /sys, this script will use the three
# variables DEV_CLASS, DEV_VENDOR, and DEV_PRODUCT to find the device file
# under /dev automatically. This behavior can be overridden by setting the
# variable DEV_NODE to the device file path. This is intended for cases, where
# either sysfs is unavailable or unusable by this script for some reason.
# Please beware that DEV_NODE must be set to None when not used, else you will
# be bitten by the NameError exception.

from pathlib import Path

import dymoprint.resources.fonts
import dymoprint.resources.icons

try:
    from pyqrcode import QRCode

    USE_QR = True
    e_qrcode = None
except ImportError as error:
    e_qrcode = error
    USE_QR = False
    QRCode = None


DESCRIPTION = (
    "Linux Software to print with LabelManager PnP from Dymo\nwritten in Python"
)
UNCONFIRMED_MESSAGE = (
    "WARNING: This device is not confirmed to work with this software. Please "
    "report your experiences in https://github.com/computerlyrik/dymoprint/issues/44"
)
SUPPORTED_PRODUCTS = {
    0x0011: "DYMO LabelMANAGER PC",
    0x0015: "LabelPoint 350",
    0x1001: "LabelManager PnP (no mode switch)",
    0x1002: "LabelManager PnP (mode switch)",
    0x1003: f"LabelManager 420P (no mode switch) {UNCONFIRMED_MESSAGE}",
    0x1004: f"LabelManager 420P (mode switch) {UNCONFIRMED_MESSAGE}",
    0x1005: "LabelManager 280 (no mode switch)",
    0x1006: "LabelManager 280 (no mode switch)",
    0x1007: f"LabelManager Wireless PnP (no mode switch) {UNCONFIRMED_MESSAGE}",
    0x1008: f"LabelManager Wireless PnP (mode switch) {UNCONFIRMED_MESSAGE}",
    0x1009: f"MobileLabeler {UNCONFIRMED_MESSAGE}",
}
DEV_VENDOR = 0x0922

PRINTER_INTERFACE_CLASS = 0x07
HID_INTERFACE_CLASS = 0x03

# Escape character preceeding all commands
ESC = 0x1B

# Synchronization character preceding uncompressed print data
SYN = 0x16

FONT_SIZERATIO = 7 / 8

DEFAULT_FONT_STYLE = "regular"

DEFAULT_MARGIN_PX = 56

FLAG_TO_STYLE = {
    "r": "regular",
    "b": "bold",
    "i": "italic",
    "n": "narrow",
}

DPI = 180
MM_PER_INCH = 25.4
PIXELS_PER_MM = DPI / MM_PER_INCH

DEFAULT_FONT_DIR = Path(dymoprint.resources.fonts.__file__).parent
ICON_DIR = Path(dymoprint.resources.icons.__file__).parent

AVAILABLE_BARCODES = [
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
]

ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"
DEPRECATION_MESSAGE_ANSI = (
    f"\n{ANSI_RED}WARNING: dymoprint is deprecated. To remove this message, either "
    f"upgrade to Labelle or downgrade to a particular version of dymoprint less "
    f"than v3.{ANSI_GREEN}\n"
    f"\n"
    f"  pipx uninstall dymoprint\n"
    f"  pipx install labelle\n"
    f"{ANSI_RED}\n"
    f"For more info, see <https://github.com/labelle-org/labelle> and "
    f"<https://github.com/computerlyrik/dymoprint/issues/114>.{ANSI_RESET}\n"
    f"\n"
)
DEPRECATION_MESSAGE_POPUP = (
    "WARNING: dymoprint is deprecated. To remove this message, either "
    "upgrade to Labelle or downgrade to a particular version of dymoprint less "
    "than v3."
    "<pre style='background-color: #f4f4f4; padding: 5px;'>"
    "pipx uninstall dymoprint\n"
    "pipx install labelle"
    "</pre>"
    "For more info, see <a href='https://github.com/labelle-org/labelle'>"
    "https://github.com/labelle-org/labelle</a> and "
    "<a href='https://github.com/computerlyrik/dymoprint/issues/114'>"
    "https://github.com/computerlyrik/dymoprint/issues/114</a>."
)
