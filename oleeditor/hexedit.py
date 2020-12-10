# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QAbstractScrollArea


class HexEdit(QAbstractScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None

    def setData(self, data):
        self._data = data

        self.update()
