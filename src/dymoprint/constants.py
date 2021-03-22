# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
from __future__ import division, print_function

try:
    from pyqrcode import QRCode
    USE_QR = True
    e_qrcode = None
except ImportError as error:
    e_qrcode = error
    USE_QR = False
    QRCode = None


DESCRIPTION = 'Linux Software to print with LabelManager PnP from Dymo\n written in Python'
DEV_CLASS       = 3
DEV_VENDOR      = 0x0922
DEV_PRODUCT     = 0x1002
#DEV_PRODUCT     = 0x1001
DEV_NODE        = None
DEV_NAME        = 'Dymo LabelManager PnP'

FONT_SIZERATIO  = 7./8
VERSION         = "1.1.1"

DEFAULT_FONT_STYLE = "regular"

FLAG_TO_STYLE = {
    "r": "regular",
    "b": "bold",
    "i": "italic",
    "n": "narrow",
}
