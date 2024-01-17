import sys
import traceback
from typing import Optional

from PIL import Image, ImageOps, ImageQt
from PyQt6 import QtCore
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from usb.core import USBError

from .constants import DEFAULT_MARGIN_PX, ICON_DIR
from .detect import detect_device
from .dymo_print_engines import DymoRenderEngine, print_label
from .q_dymo_labels_list import QDymoLabelList


class DymoPrintWindow(QWidget):
    label_bitmap: Optional[Image.Image]

    def __init__(self):
        super().__init__()
        self.render_engine = DymoRenderEngine(12)
        self.label_bitmap = None

        self.window_layout = QVBoxLayout()
        self.label_list = QDymoLabelList(self.render_engine)
        self.label_render = QLabel()
        self.error_label = QLabel()
        self.print_button = QPushButton()
        self.margin = QSpinBox()
        self.tape_size = QComboBox()
        self.foreground_color = QComboBox()
        self.background_color = QComboBox()
        self.min_label_len = QSpinBox()
        self.justify = QComboBox()

        self.init_elements()
        self.init_timers()
        self.init_connections()
        self.init_layout()

        self.label_list.render_label()

    def init_elements(self):
        self.setWindowTitle("DymoPrint GUI")
        self.setWindowIcon(QIcon(str(ICON_DIR.joinpath("gui_icon.png"))))
        self.setGeometry(200, 200, 1100, 400)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        printer_icon = QIcon.fromTheme("printer")
        self.print_button.setIcon(printer_icon)
        self.print_button.setFixedSize(64, 64)
        self.print_button.setIconSize(QSize(48, 48))

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        self.label_render.setGraphicsEffect(shadow)

        self.margin.setMinimum(20)
        self.margin.setMaximum(1000)
        self.margin.setValue(DEFAULT_MARGIN_PX)
        self.tape_size.addItem("19", 19)
        self.tape_size.addItem("12", 12)
        self.tape_size.addItem("9", 9)
        self.tape_size.addItem("6", 6)
        self.tape_size.setCurrentIndex(1)
        self.min_label_len.setMinimum(0)
        self.min_label_len.setMaximum(1000)
        self.justify.addItems(["center", "left", "right"])

        self.foreground_color.addItems(
            ["black", "white", "yellow", "blue", "red", "green"]
        )
        self.background_color.addItems(
            ["white", "black", "yellow", "blue", "red", "green"]
        )

    def init_timers(self):
        self.detected_device = None
        self.check_status()
        self.status_time = QTimer()
        self.status_time.timeout.connect(self.check_status)
        self.status_time.setInterval(2000)
        self.status_time.start(2000)

    def init_connections(self):
        self.margin.valueChanged.connect(self.label_list.render_label)
        self.tape_size.currentTextChanged.connect(self.update_params)
        self.min_label_len.valueChanged.connect(self.update_params)
        self.justify.currentTextChanged.connect(self.update_params)
        self.foreground_color.currentTextChanged.connect(self.label_list.render_label)
        self.background_color.currentTextChanged.connect(self.label_list.render_label)
        self.label_list.renderSignal.connect(self.update_label_render)
        self.print_button.clicked.connect(self.print_label)

    def init_layout(self):
        settings_widget = QToolBar(self)
        settings_widget.addWidget(QLabel("Margin:"))
        settings_widget.addWidget(self.margin)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Tape Size:"))
        settings_widget.addWidget(self.tape_size)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Min Label Len [mm]:"))
        settings_widget.addWidget(self.min_label_len)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Justify:"))
        settings_widget.addWidget(self.justify)
        settings_widget.addSeparator()
        settings_widget.addWidget(QLabel("Tape Colors: "))
        settings_widget.addWidget(self.foreground_color)
        settings_widget.addWidget(QLabel(" on "))
        settings_widget.addWidget(self.background_color)

        render_widget = QWidget(self)
        render_layout = QHBoxLayout(render_widget)
        render_layout.addWidget(self.label_render)
        render_layout.addWidget(self.error_label)
        render_layout.addWidget(self.print_button)
        render_layout.setAlignment(
            self.label_render, QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.window_layout.addWidget(settings_widget)
        self.window_layout.addWidget(self.label_list)
        self.window_layout.addWidget(render_widget)
        self.setLayout(self.window_layout)

    def update_params(self):
        self.render_engine = DymoRenderEngine(self.tape_size.currentData())
        justify = self.justify.currentText()
        min_label_mm_len: int = self.min_label_len.value()
        min_payload_len_px = max(0, (min_label_mm_len * 7) - self.margin.value() * 2)
        self.label_list.update_params(self.render_engine, min_payload_len_px, justify)

    def update_label_render(self, label_bitmap):
        self.label_bitmap = label_bitmap
        label_image = Image.new(
            "L",
            (
                self.margin.value() + label_bitmap.width + self.margin.value(),
                label_bitmap.height,
            ),
        )
        label_image.paste(label_bitmap, (self.margin.value(), 0))
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

    def print_label(self):
        try:
            if self.label_bitmap is None:
                raise RuntimeError("No label to print! Call update_label_render first.")
            print_label(
                self.detected_device, self.label_bitmap, self.margin.value(), self.tape_size.currentData()
            )
        except (RuntimeError, USBError) as err:
            print(traceback.format_exc())
            QMessageBox.warning(
                self, "Printing Failed!", f"{err}\n\n{traceback.format_exc()}"
            )

    def check_status(self):
        is_enabled = False
        try:
            self.detected_device = detect_device()
            is_enabled = True
        except Exception as e:
            self.error_label.setText(f"Error: {e}")
            self.detected_device = None
        self.error_label.setVisible(not is_enabled)
        self.print_button.setVisible(is_enabled)
        self.print_button.setEnabled(is_enabled)
        self.print_button.setCursor(Qt.CursorShape.ArrowCursor if is_enabled else Qt.CursorShape.ForbiddenCursor)


def main():
    app = QApplication(sys.argv)
    window = DymoPrintWindow()
    window.show()
    sys.exit(app.exec())
