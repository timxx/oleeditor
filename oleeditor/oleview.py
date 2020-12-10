# -*- coding: utf-8 -*-

from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTreeWidget)
from PySide2.QtCore import (
    QFileInfo)

from .hexedit import HexEdit


class OleView(QWidget):

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self._doc = doc
        title = QFileInfo(doc.path).fileName()
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)
        self._splitter = QSplitter(self)
        layout.addWidget(self._splitter)

        self._hexEdit = HexEdit(self)
        self._oleTree = QTreeWidget(self)
        self._oleTree.setHeaderHidden(True)

        self._splitter.addWidget(self._oleTree)
        self._splitter.addWidget(self._hexEdit)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 7)

        self._firstShow = False

    def getFilePath(self):
        return self._doc.path
