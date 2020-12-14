# -*- coding: utf-8 -*-

from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QTextBrowser)
from PySide2.QtCore import (
    QSize)

from .version import VERSION
from .stylehelper import dpiScaled


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(self.tr("About OLE Editor"))
        self.resize(dpiScaled(QSize(465, 300)))

        layout = QVBoxLayout(self)

        self._textBrowser = QTextBrowser(self)
        self._textBrowser.setOpenExternalLinks(True)
        layout.addWidget(self._textBrowser)

        buttonBox = QDialogButtonBox(self)
        buttonBox.setStandardButtons(QDialogButtonBox.Close)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self._initAbout()

    def _initAbout(self):
        about = "<center><h3>OLE Editor " + VERSION + "</h3></center>"
        about += "<center>"
        about += self.tr("An OLE structed storage file editor")
        about += "</center>"
        about += "<center><a href=https://github.com/timxx/oleeditor>"
        about += self.tr("Visit project host")
        about += "</a></center><br/>"
        about += "<center>Copyright © 2020 Weitian Leung</center>"

        self._textBrowser.setHtml(about)
