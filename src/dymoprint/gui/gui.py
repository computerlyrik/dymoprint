import logging
import sys
from typing import Optional

from PIL import Image, ImageOps, ImageQt
from PyQt6 import QtCore
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from usb.core import NoBackendError, USBError

from dymoprint.gui.common import crash_msg_box
from dymoprint.lib.constants import DEFAULT_MARGIN_PX, ICON_DIR
from dymoprint.lib.detect import DymoUSBError
from dymoprint.lib.dymo_labeler import (
    DymoLabeler,
)
from dymoprint.lib.logger import configure_logging, set_verbose
from dymoprint.lib.render_engines import RenderContext
from dymoprint.lib.utils import px_to_mm, system_run

from .q_dymo_labels_list import QDymoLabelList

LOG = logging.getLogger(__name__)


class DymoPrintWindow(QWidget):
    SUPPORTED_TAPE_SIZE_MM = (19, 12, 9, 6)
    DEFAULT_TAPE_SIZE_MM_INDEX = 1

    label_bitmap: Optional[Image.Image]
    dymo_labeler: DymoLabeler

    def __init__(self):
        super().__init__()
        self.label_bitmap = None
        self.detected_device = None

        self.window_layout = QVBoxLayout()
        self.render_context = RenderContext()

        self.label_list = QDymoLabelList()
        self.label_render = QLabel()
        self.error_label = QLabel()
        self.print_button = QPushButton()
        self.margin_px = QSpinBox()
        self.tape_size_mm = QComboBox()
        self.foreground_color = QComboBox()
        self.background_color = QComboBox()
        self.min_label_len_mm = QSpinBox()
        self.justify = QComboBox()
        self.info_label = QLabel()
        self.last_error = None
        self.dymo_labeler = None

        self.init_elements()
        self.init_timers()
        self.init_connections()
        self.init_layout()

        self.label_list.render_label()

    def init_elements(self):
        self.setWindowTitle("DymoPrint GUI")
        self.setWindowIcon(QIcon(str(ICON_DIR / "gui_icon.png")))
        self.setGeometry(200, 200, 1100, 400)
        printer_icon = QIcon.fromTheme("printer")
        self.print_button.setIcon(printer_icon)
        self.print_button.setFixedSize(64, 64)
        self.print_button.setIconSize(QSize(48, 48))

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        self.label_render.setGraphicsEffect(shadow)

        self.margin_px.setMinimum(20)
        self.margin_px.setMaximum(1000)
        self.margin_px.setValue(DEFAULT_MARGIN_PX)
        for tape_size_mm in self.SUPPORTED_TAPE_SIZE_MM:
            self.tape_size_mm.addItem(str(tape_size_mm), tape_size_mm)
        self.tape_size_mm.setCurrentIndex(self.DEFAULT_TAPE_SIZE_MM_INDEX)
        self.min_label_len_mm.setMinimum(0)
        self.min_label_len_mm.setMaximum(1000)
        self.justify.addItems(["center", "left", "right"])

        self.foreground_color.addItems(
            ["black", "white", "yellow", "blue", "red", "green"]
        )
        self.background_color.addItems(
            ["white", "black", "yellow", "blue", "red", "green"]
        )

        self.dymo_labeler = DymoLabeler()
        self.update_params()
        self.label_list.populate()

    def init_timers(self):
        self.check_status()
        self.status_time = QTimer()
        self.status_time.timeout.connect(self.check_status)
        self.status_time.setInterval(2000)
        self.status_time.start(2000)

    def init_connections(self):
        self.margin_px.valueChanged.connect(self.label_list.render_label)
        self.margin_px.valueChanged.connect(self.update_params)
        self.tape_size_mm.currentTextChanged.connect(self.update_params)
        self.min_label_len_mm.valueChanged.connect(self.update_params)
        self.justify.currentTextChanged.connect(self.update_params)
        self.foreground_color.currentTextChanged.connect(self.label_list.render_label)
        self.background_color.currentTextChanged.connect(self.label_list.render_label)
        self.label_list.renderSignal.connect(self.update_label_render)
        self.print_button.clicked.connect(self.print_label)

    def init_layout(self):
        settings_widget = QToolBar(self)
        settings_widget.addWidget(QLabel("Margin:"))
        settings_widget.addWidget(self.margin_px)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Tape Size:"))
        settings_widget.addWidget(self.tape_size_mm)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Min Label Len [mm]:"))
        settings_widget.addWidget(self.min_label_len_mm)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Justify:"))
        settings_widget.addWidget(self.justify)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Tape Colors: "))
        settings_widget.addWidget(self.foreground_color)
        settings_widget.addWidget(QLabel(" on "))
        settings_widget.addWidget(self.background_color)

        render_widget = QWidget(self)
        label_render_widget = QWidget(render_widget)
        print_render_widget = QWidget(render_widget)

        render_layout = QHBoxLayout(render_widget)
        label_render_layout = QVBoxLayout(label_render_widget)
        print_render_layout = QVBoxLayout(print_render_widget)
        label_render_layout.addWidget(
            self.label_render, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        label_render_layout.addWidget(
            self.info_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        print_render_layout.addWidget(
            self.print_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        print_render_layout.addWidget(
            self.error_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        render_layout.addWidget(
            label_render_widget, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        render_layout.addWidget(
            print_render_widget, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )

        self.window_layout.addWidget(settings_widget)
        self.window_layout.addWidget(self.label_list)
        self.window_layout.addWidget(render_widget)
        self.setLayout(self.window_layout)

    def update_params(self):
        justify: str = self.justify.currentText()
        margin_px: int = self.margin_px.value()
        min_label_mm_len: int = self.min_label_len_mm.value()
        tape_size_mm: int = self.tape_size_mm.currentData()

        self.dymo_labeler.margin_px = margin_px
        self.dymo_labeler.tape_size_mm = tape_size_mm
        self.render_context.height_px = self.dymo_labeler.height_px
        min_payload_len_px = max(0, (min_label_mm_len * 7) - margin_px * 2)
        self.label_list.update_params(self.render_context, min_payload_len_px, justify)

    def update_label_render(self, label_bitmap):
        self.label_bitmap = label_bitmap
        label_image = Image.new(
            "L",
            (
                self.margin_px.value() + label_bitmap.width + self.margin_px.value(),
                label_bitmap.height,
            ),
        )
        label_image.paste(label_bitmap, (self.margin_px.value(), 0))
        label_image_inv = ImageOps.invert(label_image).copy()
        qim = ImageQt.ImageQt(label_image_inv)
        q_image = QPixmap.fromImage(qim)

        mask = q_image.createMaskFromColor(
            QColor("255, 255, 255"), Qt.MaskMode.MaskOutColor
        )
        q_image.fill(QColor(self.background_color.currentText()))
        p = QPainter(q_image)
        p.setPen(QColor(self.foreground_color.currentText()))
        p.drawPixmap(q_image.rect(), mask, mask.rect())
        p.end()

        self.label_render.setPixmap(q_image)
        self.label_render.adjustSize()
        self.info_label.setText(f"← {px_to_mm(label_image.size[0])} mm →")

    def print_label(self):
        try:
            if self.label_bitmap is None:
                raise RuntimeError("No label to print! Call update_label_render first.")
            self.dymo_labeler.print(
                self.label_bitmap,
            )
        except (DymoUSBError, USBError) as err:
            crash_msg_box(self, "Printing Failed!", err)

    def check_status(self):
        self.error_label.setText("")
        try:
            self.dymo_labeler.detect()
            is_enabled = True
        except (DymoUSBError, NoBackendError, USBError) as e:
            error = str(e)
            if self.last_error != error:
                self.last_error = error
                LOG.error(error)
            self.error_label.setText(f"Error: {error}")
            is_enabled = False
        self.print_button.setEnabled(is_enabled)
        self.print_button.setCursor(
            Qt.CursorShape.ArrowCursor if is_enabled else Qt.CursorShape.ForbiddenCursor
        )


def parse(app):
    """Parse the arguments and options of the given app object."""
    parser = QCommandLineParser()
    parser.addHelpOption()

    verbose_option = QCommandLineOption(["v", "verbose"], "Verbose output.")
    parser.addOption(verbose_option)
    parser.process(app)

    is_verbose = parser.isSet(verbose_option)
    if is_verbose:
        set_verbose()


def main():
    with system_run():
        configure_logging()
        app = QApplication(sys.argv)
        parse(app)
        window = DymoPrintWindow()
        window.show()
        sys.exit(app.exec())
