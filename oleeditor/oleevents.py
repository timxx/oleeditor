# -*- coding: utf-8 -*-

from PySide2.QtCore import QEvent


class SelectionChangedEvent(QEvent):

    Type = QEvent.User + 1

    def __init__(self, view):
        super().__init__(QEvent.Type(SelectionChangedEvent.Type))
        self.view = view
