# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

from __future__ import division, print_function

import contextlib
import fcntl
import os
import re
import struct
import subprocess
import sys
import termios
import textwrap

from PIL import ImageDraw

def die(message=None):
    if message:
        print(message, file=sys.stderr)
    sys.exit(1)


def pprint(par, fd=sys.stdout):
    rows, columns = struct.unpack('HH', fcntl.ioctl(sys.stderr,
        termios.TIOCGWINSZ, struct.pack('HH', 0, 0)))
    print(textwrap.fill(par, columns), file=fd)


def getDeviceFile(classID, vendorID, productID):
    # find file containing the device's major and minor numbers
    searchdir = '/sys/bus/hid/devices'
    pattern = '^%04d:%04X:%04X.[0-9A-F]{4}$' % (classID, vendorID, productID)
    deviceCandidates = os.listdir(searchdir)
    foundpath = None
    for devname in deviceCandidates:
        if re.match(pattern, devname):
            foundpath = os.path.join(searchdir, devname)
            break
    if not foundpath:
        return
    searchdir = os.path.join(foundpath, 'hidraw')
    devname = os.listdir(searchdir)[0]
    foundpath = os.path.join(searchdir, devname)
    filepath = os.path.join(foundpath, 'dev')

    # get the major and minor numbers
    f = open(filepath, 'r')
    devnums = [int(n) for n in f.readline().strip().split(':')]
    f.close()
    devnum = os.makedev(devnums[0], devnums[1])

    # check if a symlink with the major and minor numbers is available
    filepath = '/dev/char/%d:%d' % (devnums[0], devnums[1])
    if os.path.exists(filepath):
        return os.path.realpath(filepath)

    # check if the relevant sysfs path component matches a file name in
    # /dev, that has the proper major and minor numbers
    filepath = os.path.join('/dev', devname)
    if os.stat(filepath).st_rdev == devnum:
        return filepath

    # search for a device file with the proper major and minor numbers
    for dirpath, dirnames, filenames in os.walk('/dev'):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.stat(filepath).st_rdev == devnum:
                return filepath


def access_error(dev):
    pprint('You do not have sufficient access to the device file %s:' % dev,
        sys.stderr)
    subprocess.call(['ls', '-l', dev], stdout=sys.stderr)
    print(file=sys.stderr)
    filename = "91-dymo-labelmanager-pnp.rules"
    pprint('You probably want to add a rule like one of the following in /etc/udev/rules.d/' + filename, sys.stderr)
    with open(filename, 'r') as fin:
      print(fin.read(), file=sys.stderr)
    pprint('Following that, restart udev and re-plug your device. See README.md for details', sys.stderr)


''' scaling pixel up, input: (x,y),scale-factor '''
def scaling(pix, sc):
    return [(pix[0]+i, pix[1]+j) for i in range(sc) for j in range(sc)]


''' decoding text parameter depending on system encoding '''
def to_unicode(argument_string):
    try:
        unicode  # this passes on Python 2, where we need to decode, but not on Python 3
        return argument_string.decode(sys.getfilesystemencoding())
    except NameError:
        return argument_string

@contextlib.contextmanager
def draw_image(bitmap):
    drawobj = ImageDraw.Draw(bitmap)
    try:
        yield drawobj
    finally:
        del drawobj
