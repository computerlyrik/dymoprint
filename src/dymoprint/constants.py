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
DEV_CLASS = 3
DEV_VENDOR = 0x0922
DEV_PRODUCT = 0x1002
# DEV_PRODUCT     = 0x1001
DEV_NODE = None
DEV_NAME = "Dymo LabelManager PnP"

FONT_SIZERATIO = 7 / 8

DEFAULT_FONT_STYLE = "regular"

FLAG_TO_STYLE = {
    "r": "regular",
    "b": "bold",
    "i": "italic",
    "n": "narrow",
}
