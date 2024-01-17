import traceback
from pathlib import Path
from typing import Optional

from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from dymoprint.constants import ICON_DIR
from dymoprint.dymo_print_engines import DymoRenderEngine

from .constants import AVAILABLE_BARCODES
from .font_config import parse_fonts


class FontStyle(QComboBox):
    def __init__(self):
        super(FontStyle, self).__init__()
        # Populate font_style
        for name, font_path in parse_fonts():
            self.addItem(name, font_path)
            self.setCurrentText("Carlito-Regular")


class BaseDymoLabelWidget(QWidget):
    """
    A base class for creating Dymo label widgets.
    Signals:
    --------
    itemRenderSignal : PyQtSignal
        Signal emitted when the content of the label is changed.
    Methods:
    --------
    content_changed()
        Emits the itemRenderSignal when the content of the label is changed.
    render_label()
        Abstract method to be implemented by subclasses for rendering the label.
    """

    itemRenderSignal = QtCore.pyqtSignal(name="itemRenderSignal")

    def content_changed(self):
        """
        Emits the itemRenderSignal when the content of the label is changed.
        """
        self.itemRenderSignal.emit()

    def render_label(self):
        """
        Abstract method to be implemented by subclasses for rendering the label.
        """
        pass


class TextDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering text on a Dymo label.
    Args:
        render_engine (RenderEngine): The rendering engine to use.
        parent (QWidget): The parent widget of this widget.
    Attributes:
        render_engine (RenderEngine): The rendering engine used by this widget.
        label (QPlainTextEdit): The text label to be rendered on the Dymo label.
        font_style (FontStyle): The font style selection dropdown.
        font_size (QSpinBox): The font size selection spinner.
        draw_frame (QSpinBox): The frame width selection spinner.
    Signals:
        itemRenderSignal: A signal emitted when the content of the label changes.
    """

    render_engine: DymoRenderEngine
    align: QComboBox
    label: QPlainTextEdit
    font_style: FontStyle
    font_size: QSpinBox
    draw_frame: QSpinBox

    def __init__(
        self, render_engine: DymoRenderEngine, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.render_engine = render_engine

        self.label = QPlainTextEdit("text")
        self.label.setFixedHeight(15 * (len(self.label.toPlainText().splitlines()) + 2))
        self.setFixedHeight(self.label.height() + 10)
        self.font_style = FontStyle()
        self.font_size = QSpinBox()
        self.font_size.setMaximum(150)
        self.font_size.setMinimum(0)
        self.font_size.setSingleStep(1)
        self.font_size.setValue(90)
        self.draw_frame = QSpinBox()
        self.align = QComboBox()

        self.align.addItems(["left", "center", "right"])

        layout = QHBoxLayout()
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(str(ICON_DIR / "txt_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        layout.addWidget(QLabel("Font:"))
        layout.addWidget(self.font_style)
        layout.addWidget(QLabel("Size [%]:"))
        layout.addWidget(self.font_size)
        layout.addWidget(QLabel("Frame Width:"))
        layout.addWidget(self.draw_frame)
        layout.addWidget(QLabel("Alignment:"))
        layout.addWidget(self.align)
        self.label.textChanged.connect(self.content_changed)
        self.draw_frame.valueChanged.connect(self.content_changed)
        self.font_size.valueChanged.connect(self.content_changed)
        self.font_style.currentTextChanged.connect(self.content_changed)
        self.align.currentTextChanged.connect(self.content_changed)
        self.setLayout(layout)

    def content_changed(self):
        """
        Updates the height of the label and emits the itemRenderSignal when the
        content of the label changes.
        """
        self.label.setFixedHeight(15 * (len(self.label.toPlainText().splitlines()) + 2))
        self.setFixedHeight(self.label.height() + 10)
        self.itemRenderSignal.emit()

    def render_label(self):
        """
        Renders the label using the current settings.
        Returns:
            QImage: The rendered label image.
        Raises:
            QMessageBox.warning: If the rendering fails.
        """
        selected_alignment = self.align.currentText()
        assert selected_alignment in ("left", "center", "right")
        try:
            return self.render_engine.render_text(
                text_lines=self.label.toPlainText().splitlines(),
                font_file_name=self.font_style.currentData(),
                frame_width_px=self.draw_frame.value(),
                font_size_ratio=self.font_size.value() / 100.0,
                align=selected_alignment,
            )
        except BaseException as err:
            QMessageBox.warning(self, "TextDymoLabelWidget render fail!", traceback.format_exc())
            return self.render_engine.render_empty()


class QrDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering QR codes on Dymo labels.
    Args:
        render_engine (RenderEngine): The render engine to use for rendering
            the QR code.
        parent (QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, render_engine, parent=None):
        """
        Initializes the QrDymoLabelWidget.
        Args:
            render_engine (RenderEngine): The render engine to use for rendering
                the QR code.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.render_engine = render_engine

        self.label = QLineEdit("")
        layout = QHBoxLayout()
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(str(ICON_DIR / "qr_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        self.label.textChanged.connect(self.content_changed)
        self.setLayout(layout)

    def render_label(self):
        """
        Renders the QR code on the Dymo label.
        Returns:
            bytes: The rendered QR code as bytes.
        Raises:
            QMessageBox.warning: If the rendering fails.
        """
        try:
            return self.render_engine.render_qr(self.label.text())
        except BaseException as err:
            QMessageBox.warning(self, "QrDymoLabelWidget render fail!", traceback.format_exc())
            return self.render_engine.render_empty()


class BarcodeDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering barcode labels using the Dymo label printer.
    Args:
        render_engine (DymoRenderEngine): An instance of the DymoRenderEngine class.
        parent (QWidget): The parent widget of this widget.
    Attributes:
        render_engine (DymoRenderEngine): An instance of the DymoRenderEngine class.
        label (QLineEdit): A QLineEdit widget for entering the content of the
            barcode label.
        Type (QComboBox): A QComboBox widget for selecting the type of barcode
            to render.
        font_style (FontStyle): The font style selection dropdown.
        font_size (QSpinBox): The font size selection spinner.
        draw_frame (QSpinBox): The frame width selection spinner.
    Signals:
        content_changed(): Emitted when the content of the label or the selected
            barcode type changes.
    Methods:
        __init__(self, render_engine, parent=None): Initializes the widget.
        render_label(self): Renders the barcode label using the current content
            and barcode type.
    """

    render_engine: DymoRenderEngine
    label: QLineEdit
    barcode_type_label: QLabel
    barcode_type: QComboBox
    show_text_label: QLabel
    show_text_checkbox: QCheckBox
    font_style: FontStyle
    font_size: QSpinBox
    draw_frame: QSpinBox
    font_label: QLabel
    size_label: QLabel
    frame_label: QLabel
    align_label: QLabel
    align: QComboBox

    def __init__(self, render_engine, parent=None):
        super().__init__(parent)
        self.render_engine = render_engine

        self.label = QLineEdit("")

        # Hidable text fields and their labels
        self.font_label = QLabel("Font:")
        self.font_style = FontStyle()
        self.size_label = QLabel("Size [%]:")
        self.font_size = QSpinBox()
        self.font_size.setMaximum(150)
        self.font_size.setMinimum(0)
        self.font_size.setSingleStep(1)
        self.font_size.setValue(90)
        self.frame_label = QLabel("Frame Width:")
        self.draw_frame = QSpinBox()
        self.align_label = QLabel("Alignment:")
        self.align = QComboBox()
        self.item_icon = QLabel()
        self.item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.align.addItems(["left", "center", "right"])
        # Set the default value to "center"
        self.align.setCurrentIndex(1)

        self.set_text_fields_visibility(True)

        layout = QHBoxLayout()

        self.barcode_type_label = QLabel("Type:")
        self.barcode_type = QComboBox()
        self.barcode_type.addItems(AVAILABLE_BARCODES)

        # Checkbox for toggling text fields
        self.show_text_label = QLabel("Text:")
        self.show_text_checkbox = QCheckBox()
        self.show_text_checkbox.setChecked(True)
        self.show_text_checkbox.stateChanged.connect(
            self.toggle_text_fields_and_rerender
        )

        layout.addWidget(self.item_icon)
        layout.addWidget(self.label)
        layout.addWidget(self.barcode_type_label)
        layout.addWidget(self.barcode_type)
        layout.addWidget(self.show_text_label)
        layout.addWidget(self.show_text_checkbox)
        layout.addWidget(self.font_label)
        layout.addWidget(self.font_style)
        layout.addWidget(self.size_label)
        layout.addWidget(self.font_size)
        layout.addWidget(self.frame_label)
        layout.addWidget(self.draw_frame)
        layout.addWidget(self.align_label)
        layout.addWidget(self.align)

        self.label.textChanged.connect(self.content_changed)
        self.draw_frame.valueChanged.connect(self.content_changed)
        self.font_size.valueChanged.connect(self.content_changed)
        self.font_style.currentTextChanged.connect(self.content_changed)
        self.align.currentTextChanged.connect(self.content_changed)
        self.barcode_type.currentTextChanged.connect(self.content_changed)

        self.setLayout(layout)

    def set_text_fields_visibility(self, visible):
        self.font_label.setVisible(visible)
        self.font_style.setVisible(visible)
        self.size_label.setVisible(visible)
        self.font_size.setVisible(visible)
        self.frame_label.setVisible(visible)
        self.draw_frame.setVisible(visible)
        self.align_label.setVisible(visible)
        self.align.setVisible(visible)
        if visible:
            self.item_icon.setPixmap(
                QIcon(str(ICON_DIR / "barcode_text_icon.png")).pixmap(32, 32)
            )
        else:
            self.item_icon.setPixmap(
                QIcon(str(ICON_DIR / "barcode_icon.png")).pixmap(32, 32)
            )

    def toggle_text_fields_and_rerender(self):
        is_checked = self.show_text_checkbox.isChecked()
        self.set_text_fields_visibility(is_checked)
        self.content_changed()  # Trigger rerender

    def render_label(self):
        """
        Renders the labels with barcode and text below it using the current settings.
        Returns:
            QImage: The rendered label image.
        Raises:
            QMessageBox.warning: If the rendering fails.
        """
        try:
            if self.show_text_checkbox.isChecked():
                return self.render_engine.render_barcode_with_text(
                    barcode_input_text=self.label.text(),
                    bar_code_type=self.barcode_type.currentText(),
                    font_file_name=self.font_style.currentData(),
                    frame_width=self.draw_frame.value(),
                    font_size_ratio=self.font_size.value() / 100.0,
                    align=self.align.currentText(),
                )
            else:
                return self.render_engine.render_barcode(
                    self.label.text(), self.barcode_type.currentText()
                )
        except BaseException as err:
            QMessageBox.warning(self, "BarcodeDymoLabelWidget render fail!", traceback.format_exc())
            return self.render_engine.render_empty()


class ImageDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering image-based Dymo labels.
    Args:
        render_engine (RenderEngine): The render engine to use for rendering the label.
        parent (QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, render_engine, parent=None):
        """
        Initializes the ImageDymoLabelWidget.
        Args:
            render_engine (RenderEngine): The render engine to use for rendering
                the label.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.render_engine = render_engine

        self.label = QLineEdit("")
        layout = QHBoxLayout()
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(str(ICON_DIR / "img_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        button = QPushButton("Select file")
        file_dialog = QFileDialog()
        button.clicked.connect(
            lambda: self.label.setText(
                str(Path(file_dialog.getOpenFileName()[0]).absolute())
            )
        )

        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        layout.addWidget(button)

        self.label.textChanged.connect(self.content_changed)
        self.setLayout(layout)

    def render_label(self):
        """
        Renders the label using the render engine and the selected image file.
        Returns:
            QPixmap: The rendered label as a QPixmap.
        """
        try:
            return self.render_engine.render_picture(self.label.text())
        except BaseException as err:
            QMessageBox.warning(self, "ImageDymoLabelWidget render fail!", traceback.format_exc())
            return self.render_engine.render_empty()
