import logging
from typing import Optional

from PIL import Image
from PyQt6 import QtCore
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QMenu

from dymoprint.gui.common import crash_msg_box
from dymoprint.gui.q_dymo_label_widgets import (
    BarcodeDymoLabelWidget,
    EmptyRenderEngine,
    ImageDymoLabelWidget,
    QrDymoLabelWidget,
    TextDymoLabelWidget,
)
from dymoprint.lib.render_engines import HorizontallyCombinedRenderEngine, RenderContext

LOG = logging.getLogger(__name__)


class QDymoLabelList(QListWidget):
    """A custom QListWidget for displaying and managing Dymo label widgets.

    Args:
    ----
        render_context (RenderContext): The render context to use for rendering the
        label.
        parent (QWidget): The parent widget of this QListWidget.

    Attributes:
    ----------
        renderSignal (QtCore.pyqtSignal): A signal emitted when the label is rendered.
        render_context (RenderContext): The render context used for rendering the label.

    Methods:
    -------
        __init__(self, render_context, parent=None): Initializes the QListWidget
            with the given render context and parent.
        dropEvent(self, e) -> None: Overrides the default drop event to update
            the label rendering.
        update_render_engine(self, render_engine): Updates the render context used
            for rendering the label.
        render_label(self): Renders the label using the current render context and
            emits the renderSignal.
        contextMenuEvent(self, event): Overrides the default context menu event to
            add or delete label widgets.
    """

    renderSignal = QtCore.pyqtSignal(Image.Image, name="renderSignal")
    render_context: Optional[RenderContext]
    itemWidget: TextDymoLabelWidget

    def __init__(self, min_payload_len_px=0, justify="center", parent=None):
        super().__init__(parent)
        self.min_payload_len_px = min_payload_len_px
        self.justify = justify
        self.render_context = None
        self.setAlternatingRowColors(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def populate(self):
        for item_widget in [TextDymoLabelWidget(self.render_context)]:
            item = QListWidgetItem(self)
            item.setSizeHint(item_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, item_widget)
            item_widget.itemRenderSignal.connect(self.render_label)

    def dropEvent(self, e) -> None:
        """Override the default drop event to update the label rendering.

        Args:
        ----
            e (QDropEvent): The drop event.
        """
        super().dropEvent(e)
        self.render_label()

    def update_params(
        self,
        render_context: RenderContext,
        min_payload_len_px: int,
        justify="center",
    ):
        """Update the render context used for rendering the label.

        Args:
        ----
            justify: justification [center,left,right]
            min_payload_len_px: minimum payload size in pixels
            render_context (RenderContext): The new render context to use.
        """
        self.min_payload_len_px = min_payload_len_px
        self.justify = justify
        self.render_context = render_context
        for i in range(self.count()):
            item_widget = self.itemWidget(self.item(i))
            item_widget.render_context = render_context
        self.render_label()

    @property
    def render_engines(self):
        engines = []
        for i in range(self.count()):
            item = self.item(i)
            item_widget = self.itemWidget(self.item(i))
            if item_widget and item:
                item.setSizeHint(item_widget.sizeHint())
                engines.append(item_widget.render_engine)
        return engines

    def render_label(self):
        """Render the label using the current render context and emit renderSignal."""
        render_engine = HorizontallyCombinedRenderEngine(
            render_engines=self.render_engines,
            min_payload_len_px=self.min_payload_len_px,
            max_payload_len_px=None,
            justify=self.justify,
        )
        try:
            label_bitmap = render_engine.render(self.render_context)
        except BaseException as err:  # noqa: BLE001
            crash_msg_box(self, "Render Engine Failed!", err)
            label_bitmap = EmptyRenderEngine().render(self.render_context)

        self.renderSignal.emit(label_bitmap)

    def contextMenuEvent(self, event):
        """Override the default context menu event to add or delete label widgets.

        Args:
        ----
            event (QContextMenuEvent): The context menu event.
        """
        contextMenu = QMenu(self)
        add_text: Optional[QAction] = contextMenu.addAction("Add Text")
        add_qr: Optional[QAction] = contextMenu.addAction("Add QR")
        add_barcode: Optional[QAction] = contextMenu.addAction("Add Barcode")
        add_img: Optional[QAction] = contextMenu.addAction("Add Image")
        delete: Optional[QAction] = contextMenu.addAction("Delete")
        menu_click = contextMenu.exec(event.globalPos())

        if menu_click == add_text:
            item = QListWidgetItem(self)
            item_widget = TextDymoLabelWidget(self.render_context)
            item.setSizeHint(item_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, item_widget)
            item_widget.itemRenderSignal.connect(self.render_label)

        if menu_click == add_qr:
            item = QListWidgetItem(self)
            item_widget = QrDymoLabelWidget(self.render_context)
            item.setSizeHint(item_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, item_widget)
            item_widget.itemRenderSignal.connect(self.render_label)

        if menu_click == add_barcode:
            item = QListWidgetItem(self)
            item_widget = BarcodeDymoLabelWidget(self.render_context)
            item.setSizeHint(item_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, item_widget)
            item_widget.itemRenderSignal.connect(self.render_label)

        if menu_click == add_img:
            item = QListWidgetItem(self)
            item_widget = ImageDymoLabelWidget(self.render_context)
            item.setSizeHint(item_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, item_widget)
            item_widget.itemRenderSignal.connect(self.render_label)
        if menu_click == delete:
            try:
                item_to_delete = self.itemAt(event.pos())
                self.takeItem(self.indexFromItem(item_to_delete).row())  # self.update()
            except Exception as e:  # noqa: BLE001
                LOG.warning(f"No item selected {e}")
        self.render_label()
