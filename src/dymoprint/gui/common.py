import traceback

from PyQt6.QtWidgets import (
    QMessageBox,
)

from dymoprint.lib.utils import is_debug_mode, print_exception


def crash_msg_box(parent, title, err):
    if is_debug_mode():
        print(traceback.format_exc())
    else:
        print_exception(err)
    QMessageBox.warning(parent, title, f"{err}\n\n{traceback.format_exc()}")
