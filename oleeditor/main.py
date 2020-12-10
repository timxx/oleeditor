# -*- coding: utf-8 -*-

from .oleapp import OleApp
from .olewindow import OleWindow

from PySide2.QtCore import (
    QCoreApplication,
    QThread,
    Qt)
from PySide2.QtWidgets import (
    QMessageBox,
    QStyle)

import sys
import traceback


def QtExceptHandler(etype, value, tb):
    if QCoreApplication.instance().thread() == QThread.currentThread():
        msg = traceback.format_exception(etype, value, tb)
        QMessageBox.warning(None, "Exception occurred!",
                            "".join(msg), QMessageBox.Ok)
    else:
        traceback.print_exception(etype, value, tb)


def main():
    app = OleApp(sys.argv)

    sys.excepthook = QtExceptHandler

    window = OleWindow()
    window.setGeometry(QStyle.alignedRect(
        Qt.LeftToRight, Qt.AlignCenter,
        window.size(),
        qApp.desktop().availableGeometry()))
    window.show()

    return app.exec_()


if __name__ == "__main__":
    main()
