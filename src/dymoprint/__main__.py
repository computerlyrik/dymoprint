#!/usr/bin/env python

# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
#
# On systems with access to sysfs under /sys, this script will use the three
# variables DEV_CLASS, DEV_VENDOR, and DEV_PRODUCT to find the device file
# under /dev automatically. This behavior can be overridden by setting the
# variable DEV_NODE to the device file path. This is intended for cases, where
# either sysfs is unavailable or unusable by this script for some reason.
# Please beware that DEV_NODE must be set to None when not used, else you will
# be bitten by the NameError exception.

from __future__ import division, print_function

import sys

from .command_line import main, parse_args


def main_with_debug():
    args = parse_args()
    try:
        main(args)
    except:
        if not args.pdb:
            raise
        import traceback
        import pdb
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

if __name__ == '__main__':
    main_with_debug()
