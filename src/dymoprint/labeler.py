# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
import array
from typing import List, Optional

import usb

from .constants import DEFAULT_MARGIN_PX, ESC, SYN


class DymoLabeler:
    """Create and work with a Dymo LabelManager PnP object.

    This class contains both mid-level and high-level functions. In general,
    the high-level functions should be used. However, special purpose usage
    may require the mid-level functions. That is why they are provided.
    However, they should be well understood before use. Look at the
    high-level functions for help. Each function is marked in its docstring
    with 'HLF' or 'MLF' in parentheses.

    A partial reference of the protocol is the Technical Reference for the
    LabelWriter 450:
    <https://download.dymo.com/dymo/technical-data-sheets/LW%20450%20Series%20Technical%20Reference.pdf>
    """

    tape_size_mm: int

    @staticmethod
    def max_bytes_per_line(tape_size_mm: int = 12) -> int:
        return int(8 * tape_size_mm / 12)

    # Max number of print lines to send before waiting for a response. This helps
    # to avoid timeouts due to differences between data transfer and
    # printer speeds. I added this because I kept getting "IOError: [Errno
    # 110] Connection timed out" with long labels. Using dev.default_timeout
    # (1000) and the transfer speeds available in the descriptors somewhere, a
    # sensible timeout can also be calculated dynamically.
    synwait: Optional[int]
    devout: usb.core.Endpoint
    devin: usb.core.Endpoint

    def __init__(self, devout, devin, synwait=None, tape_size_mm=12):
        """Initialize the LabelManager object (HLF)."""
        self.tape_size_mm = tape_size_mm
        self.cmd: List[int] = []
        self.response = False
        self.bytesPerLine_ = None
        self.dotTab_ = 0
        self.maxLines = 200
        self.devout = devout
        self.devin = devin
        self.synwait = synwait

    def sendCommand(self):
        """Send the already built command to the LabelManager (MLF)."""
        if len(self.cmd) == 0:
            return None

        while len(self.cmd) > 0:
            if self.synwait is None:
                cmd_to_send = self.cmd
                cmd_rest = []
            else:
                # Send a status request
                cmdBin = array.array("B", [ESC, ord("A")])
                cmdBin.tofile(self.devout)
                rspBin = self.devin.read(8)
                _ = array.array("B", rspBin).tolist()
                # Ok, we got a response. Now we can send a chunk of data

                # Compute a chunk with at most synwait SYN characters
                synCount = 0  # Number of SYN characters encountered in iteration
                pos = -1  # Index of last SYN character encountered in iteration
                while synCount < self.synwait:
                    try:
                        # Increment pos to the index of the next SYN character
                        pos += self.cmd[pos + 1 :].index(SYN) + 1
                        synCount += 1
                    except ValueError:
                        # No more SYN characters in cmd
                        pos = len(self.cmd)
                        break
                cmd_to_send = self.cmd[:pos]
                cmd_rest = self.cmd[pos:]
                print(f"Sending chunk of {len(cmd_to_send)} bytes")

            # Remove the computed chunk from the command to be processed
            self.cmd = cmd_rest

            # Send the chunk
            cmdBin = array.array("B", cmd_to_send)
            cmdBin.tofile(self.devout)

        self.cmd = []  # This looks redundant.
        if not self.response:
            return None
        self.response = False
        responseBin = self.devin.read(8)
        response = array.array("B", responseBin).tolist()
        return response

    def resetCommand(self):
        """Remove a partially built command (MLF)."""
        self.cmd = []
        self.response = False

    def buildCommand(self, cmd):
        """Add the next instruction to the command (MLF)."""
        self.cmd += cmd

    def statusRequest(self):
        """Set instruction to get the device's status (MLF)."""
        cmd = [ESC, ord("A")]
        self.buildCommand(cmd)
        self.response = True

    def dotTab(self, value):
        """Set the bias text height, in bytes (MLF)."""
        if value < 0 or value > self.max_bytes_per_line(self.tape_size_mm):
            raise ValueError
        cmd = [ESC, ord("B"), value]
        self.buildCommand(cmd)
        self.dotTab_ = value
        self.bytesPerLine_ = None

    def tapeColor(self, value):
        """Set the tape color (MLF)."""
        if value < 0:
            raise ValueError
        cmd = [ESC, ord("C"), value]
        self.buildCommand(cmd)

    def bytesPerLine(self, value: int):
        """Set the number of bytes sent in the following lines (MLF)."""
        if value == self.bytesPerLine_:
            return
        cmd = [ESC, ord("D"), value]
        self.buildCommand(cmd)
        self.bytesPerLine_ = value

    def cut(self):
        """Set instruction to trigger cutting of the tape (MLF)."""
        cmd = [ESC, ord("E")]
        self.buildCommand(cmd)

    def line(self, value):
        """Set next printed line (MLF)."""
        self.bytesPerLine(len(value))
        cmd = [SYN, *value]
        self.buildCommand(cmd)

    def chainMark(self):
        """Set Chain Mark (MLF)."""
        self.dotTab(0)
        self.bytesPerLine(self.max_bytes_per_line(self.tape_size_mm))
        self.line([0x99] * self.max_bytes_per_line(self.tape_size_mm))

    def skipLines(self, value):
        """Set number of lines of white to print (MLF)."""
        if value <= 0:
            raise ValueError
        self.bytesPerLine(0)
        cmd = [SYN] * value
        self.buildCommand(cmd)

    def initLabel(self):
        """Set the label initialization sequence (MLF).

        This was in the original dymoprint by S. Bronner but was never invoked.
        (There was a self.initLabel without parentheses.)
        I see no mention of it in the technical reference, so this seems to be
        dead code.
        """
        cmd = [0x00] * 8
        self.buildCommand(cmd)

    def getStatus(self):
        """Ask for and return the device's status (HLF)."""
        self.statusRequest()
        response = self.sendCommand()
        print(response)

    def printLabel(self, lines: List[List[int]], margin_px=DEFAULT_MARGIN_PX):
        """Print the label described by lines.

        Automatically split the label if it's larger than maxLines.
        """
        while len(lines) > self.maxLines + 1:
            self.rawPrintLabel(lines[0 : self.maxLines], margin_px=0)
            del lines[0 : self.maxLines]
        self.rawPrintLabel(lines, margin_px=margin_px)

    def rawPrintLabel(self, lines: List[List[int]], margin_px=DEFAULT_MARGIN_PX):
        """Print the label described by lines (HLF)."""
        # Here used to be a matrix optimization code that caused problems in issue #87
        self.tapeColor(0)
        for line in lines:
            self.line(line)
        if margin_px > 0:
            self.skipLines(margin_px * 2)
        self.statusRequest()
        response = self.sendCommand()
        print(f"Post-send response: {response}")
