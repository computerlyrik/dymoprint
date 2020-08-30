# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
from __future__ import division, print_function

import array


class DymoLabeler:
    """Create and work with a Dymo LabelManager PnP object.

    This class contains both mid-level and high-level functions. In general,
    the high-level functions should be used. However, special purpose usage
    may require the mid-level functions. That is why they are provided.
    However, they should be well understood before use. Look at the
    high-level functions for help. Each function is marked in its docstring
    with 'HLF' or 'MLF' in parentheses.
    """

    _ESC = 0x1b
    _SYN = 0x16
    _MAX_BYTES_PER_LINE = 8  # 64 pixels on a 12mm tape

    def __init__(self, dev):
        """Initialize the LabelManager object. (HLF)"""

        self.cmd = []
        self.response = False
        self.bytesPerLine_ = None
        self.dotTab_ = 0
        self.dev = open(dev, 'rb+')
        self.maxLines = 200

    def sendCommand(self):
        """Send the already built command to the LabelManager. (MLF)"""

        if len(self.cmd) == 0:
            return
        cmdBin = array.array('B', self.cmd)
        cmdBin.tofile(self.dev)
        self.cmd = []
        if not self.response:
            return
        self.response = False
        responseBin = self.dev.read(8)
        response = array.array('B', responseBin).tolist()
        return response

    def resetCommand(self):
        """Remove a partially built command. (MLF)"""

        self.cmd = []
        self.response = False

    def buildCommand(self, cmd):
        """Add the next instruction to the command. (MLF)"""

        self.cmd += cmd

    def statusRequest(self):
        """Set instruction to get the device's status. (MLF)"""

        cmd = [self._ESC, ord('A')]
        self.buildCommand(cmd)
        self.response = True

    def dotTab(self, value):
        """Set the bias text height, in bytes. (MLF)"""

        if value < 0 or value > self._MAX_BYTES_PER_LINE:
            raise ValueError
        cmd = [self._ESC, ord('B'), value]
        self.buildCommand(cmd)
        self.dotTab_ = value
        self.bytesPerLine_ = None

    def tapeColor(self, value):
        """Set the tape color. (MLF)"""

        if value < 0: raise ValueError
        cmd = [self._ESC, ord('C'), value]
        self.buildCommand(cmd)

    def bytesPerLine(self, value):
        """Set the number of bytes sent in the following lines. (MLF)"""

        if value < 0 or value + self.dotTab_ > self._MAX_BYTES_PER_LINE:
            raise ValueError
        if value == self.bytesPerLine_:
            return
        cmd = [self._ESC, ord('D'), value]
        self.buildCommand(cmd)
        self.bytesPerLine_ = value

    def cut(self):
        """Set instruction to trigger cutting of the tape. (MLF)"""

        cmd = [self._ESC, ord('E')]
        self.buildCommand(cmd)

    def line(self, value):
        """Set next printed line. (MLF)"""

        self.bytesPerLine(len(value))
        cmd = [self._SYN] + value
        self.buildCommand(cmd)

    def chainMark(self):
        """Set Chain Mark. (MLF)"""

        self.dotTab(0)
        self.bytesPerLine(self._MAX_BYTES_PER_LINE)
        self.line([0x99] * self._MAX_BYTES_PER_LINE)

    def skipLines(self, value):
        """Set number of lines of white to print. (MLF)"""

        if value <= 0:
            raise ValueError
        self.bytesPerLine(0)
        cmd = [self._SYN] * value
        self.buildCommand(cmd)

    def initLabel(self):
        """Set the label initialization sequence. (MLF)"""

        cmd = [0x00] * 8
        self.buildCommand(cmd)

    def getStatus(self):
        """Ask for and return the device's status. (HLF)"""

        self.statusRequest()
        response = self.sendCommand()
        print(response)

    def printLabel(self, lines, margin=56*2):
        """Print the label described by lines. (Automatically split label if 
           larger than maxLines)"""

        while len(lines) > self.maxLines + 1:
            self.rawPrintLabel(lines[0:self.maxLines], margin=0)
            del lines[0:self.maxLines]
        self.rawPrintLabel(lines, margin=margin)

    def rawPrintLabel(self, lines, margin=56*2):
        """Print the label described by lines. (HLF)"""

        # optimize the matrix for the dymo label printer
        dottab = 0
        while [] not in lines and max(line[0] for line in lines) == 0:
            lines = [line[1:] for line in lines]
            dottab += 1
        for line in lines:
            while len(line) > 0 and line[-1] == 0:
                del line[-1]

        self.initLabel
        self.tapeColor(0)
        self.dotTab(dottab)
        for line in lines:
            self.line(line)
        if margin > 0:
            self.skipLines(margin)
        self.statusRequest()
        response = self.sendCommand()
        print(response)
