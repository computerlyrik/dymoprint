# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

try:
    from pyqrcode import QRCode
    USE_QR = True
except ImportError as error:
    e_qrcode = error
    USE_QR = False
try:
    import barcode
    USE_BARCODE = True
except ImportError as error:
    e_barcode = error
    USE_BARCODE = False


DESCRIPTION = 'Linux Software to print with LabelManager PnP from Dymo\n written in Python'
DEV_CLASS       = 3
DEV_VENDOR      = 0x0922
DEV_PRODUCT     = 0x1002
#DEV_PRODUCT     = 0x1001
DEV_NODE        = None
DEV_NAME        = 'Dymo LabelManager PnP'
#FONT_FILENAME  = '/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf'
FONT_CONFIG = {'regular':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-R.ttf',     # regular font
               'bold':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-B.ttf',        # bold font
               'italic':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-RI.ttf',       # italic font
               'narrow':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-C.ttf'    # narrow/condensed
               }
FONT_SIZERATIO  = 7./8
#CONFIG_FILE     = '.dymoprint'
CONFIG_FILE     = 'dymoprint.ini'
VERSION         = "0.3.4 (2016-03-14)"
