# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
from __future__ import annotations

import array
import logging

import usb

from .constants import DEFAULT_MARGIN_PX, ESC, SYN

LOG = logging.getLogger(__name__)


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

    DEFAULT_TAPE_SIZE_MM = 12

    tape_size_mm: int

    # Max number of print lines to send before waiting for a response. This helps
    # to avoid timeouts due to differences between data transfer and
    # printer speeds. I added this because I kept getting "IOError: [Errno
    # 110] Connection timed out" with long labels. Using dev.default_timeout
    # (1000) and the transfer speeds available in the descriptors somewhere, a
    # sensible timeout can also be calculated dynamically.
    _synwait: int | None
    _bytesPerLine: int | None
    _devout: usb.core.Endpoint
    _devin: usb.core.Endpoint

    def __init__(
        self,
        devout: usb.core.Endpoint,
        devin: usb.core.Endpoint,
        synwait: int | None = None,
        tape_size_mm: int | None = None,
    ):
        """Initialize the LabelManager object (HLF)."""
        if not tape_size_mm:
            tape_size_mm = self.DEFAULT_TAPE_SIZE_MM
        self._tape_size_mm = tape_size_mm
        self._cmd: list[int] = []
        self._response = False
        self._bytesPerLine = None
        self._dotTab = 0
        self._maxLines = 200
        self._devout = devout
        self._devin = devin
        self._synwait = synwait

    @classmethod
    def _max_bytes_per_line(cls, tape_size_mm: int | None = None) -> int:
        if not tape_size_mm:
            tape_size_mm = cls.DEFAULT_TAPE_SIZE_MM
        return int(8 * tape_size_mm / 12)

    @classmethod
    def height_px(cls, tape_size_mm: int | None = None):
        return cls._max_bytes_per_line(tape_size_mm) * 8

    def _send_command(self):
        """Send the already built command to the LabelManager (MLF)."""
        if len(self._cmd) == 0:
            return None

        while len(self._cmd) > 0:
            if self._synwait is None:
                cmd_to_send = self._cmd
                cmd_rest = []
            else:
                # Send a status request
                cmdBin = array.array("B", [ESC, ord("A")])
                cmdBin.tofile(self._devout)
                rspBin = self._devin.read(8)
                _ = array.array("B", rspBin).tolist()
                # Ok, we got a response. Now we can send a chunk of data

                # Compute a chunk with at most synwait SYN characters
                synCount = 0  # Number of SYN characters encountered in iteration
                pos = -1  # Index of last SYN character encountered in iteration
                while synCount < self._synwait:
                    try:
                        # Increment pos to the index of the next SYN character
                        pos += self._cmd[pos + 1 :].index(SYN) + 1
                        synCount += 1
                    except ValueError:
                        # No more SYN characters in cmd
                        pos = len(self._cmd)
                        break
                cmd_to_send = self._cmd[:pos]
                cmd_rest = self._cmd[pos:]
                LOG.debug(f"Sending chunk of {len(cmd_to_send)} bytes")

            # Remove the computed chunk from the command to be processed
            self._cmd = cmd_rest

            # Send the chunk
            cmdBin = array.array("B", cmd_to_send)
            cmdBin.tofile(self._devout)

        self._cmd = []  # This looks redundant.
        if not self._response:
            return None
        self._response = False
        responseBin = self._devin.read(8)
        response = array.array("B", responseBin).tolist()
        return response

    def _reset_command(self):
        """Remove a partially built command (MLF)."""
        self._cmd = []
        self._response = False

    def _build_command(self, cmd):
        """Add the next instruction to the command (MLF)."""
        self._cmd += cmd

    def _status_request(self):
        """Set instruction to get the device's status (MLF)."""
        cmd = [ESC, ord("A")]
        self._build_command(cmd)
        self._response = True

    def _dot_tab(self, value):
        """Set the bias text height, in bytes (MLF)."""
        if value < 0 or value > self._max_bytes_per_line(self._tape_size_mm):
            raise ValueError
        cmd = [ESC, ord("B"), value]
        self._build_command(cmd)
        self._dotTab = value
        self._bytesPerLine = None

    def _tape_color(self, value):
        """Set the tape color (MLF)."""
        if value < 0:
            raise ValueError
        cmd = [ESC, ord("C"), value]
        self._build_command(cmd)

    def _bytes_per_line(self, value: int):
        """Set the number of bytes sent in the following lines (MLF)."""
        if value == self._bytesPerLine:
            return
        cmd = [ESC, ord("D"), value]
        self._build_command(cmd)
        self._bytesPerLine = value

    def _cut(self):
        """Set instruction to trigger cutting of the tape (MLF)."""
        cmd = [ESC, ord("E")]
        self._build_command(cmd)

    def _line(self, value):
        """Set next printed line (MLF)."""
        self._bytes_per_line(len(value))
        cmd = [SYN, *value]
        self._build_command(cmd)

    def _chain_mark(self):
        """Set Chain Mark (MLF)."""
        self._dot_tab(0)
        self._bytes_per_line(self._max_bytes_per_line(self._tape_size_mm))
        self._line([0x99] * self._max_bytes_per_line(self._tape_size_mm))

    def _skip_lines(self, value):
        """Set number of lines of white to print (MLF)."""
        if value <= 0:
            raise ValueError
        self._bytes_per_line(0)
        cmd = [SYN] * value
        self._build_command(cmd)

    def _init_label(self):
        """Set the label initialization sequence (MLF).

        This was in the original dymoprint by S. Bronner but was never invoked.
        (There was a self.initLabel without parentheses.)
        I see no mention of it in the technical reference, so this seems to be
        dead code.
        """
        cmd = [0x00] * 8
        self._build_command(cmd)

    def _get_status(self):
        """Ask for and return the device's status (HLF)."""
        self._status_request()
        return self._send_command()

    def print_label(self, lines: list[list[int]], margin_px=DEFAULT_MARGIN_PX):
        """Print the label described by lines.

        Automatically split the label if it's larger than maxLines.
        """
        while len(lines) > self._maxLines + 1:
            self._raw_print_label(lines[0 : self._maxLines], margin_px=0)
            del lines[0 : self._maxLines]
        self._raw_print_label(lines, margin_px=margin_px)

    def _raw_print_label(self, lines: list[list[int]], margin_px=DEFAULT_MARGIN_PX):
        """Print the label described by lines (HLF)."""
        # Here used to be a matrix optimization code that caused problems in issue #87
        self._tape_color(0)
        for line in lines:
            self._line(line)
        if margin_px > 0:
            self._skip_lines(margin_px * 2)
        self._status_request()
        status = self._get_status()
        LOG.debug(f"Post-send response: {status}")
