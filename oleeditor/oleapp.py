# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QApplication


class OleApp(QApplication):

    def __init__(self, argv):
        super().__init__(argv)
