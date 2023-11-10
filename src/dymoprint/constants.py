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

# Print offset dictionaries
# The three values indicate:
# - Printer header size in dots
# - A number of the first visible dot on a test print,
# - A number of the last visible dot on a test print.
# Note the dot numeration is zero based.
# Impossible combinations (such as PnP with 19mm tape) should have sane defaults.
dict_pnp  = {6: (64,11,51), 9: (64,1,62),  12: (64,0,63),   19: (64,0,63)}
dict_420p = {6: (128,44,85), 9: (128,31,94), 12: (128,38,117), 19: (128,2,127)}

# Offset meta-dictionary
# This one binds printer PID with an offset dictionary.
# All supported products must have an entry here.
OFFSETS = {
    0x0011: dict_pnp,
    0x0015: dict_pnp,
    0x1001: dict_pnp,
    0x1002: dict_pnp,
    0x1003: dict_420p,
    0x1004: dict_420p,
    0x1005: dict_pnp,
    0x1006: dict_pnp,
    0x1007: dict_pnp,
    0x1008: dict_pnp,
    0x1009: dict_pnp
}

