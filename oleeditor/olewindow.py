# -*- coding: utf-8 -*-


from PySide2.QtWidgets import (
    QMainWindow,
    QMdiArea,
    QTabBar,
    QFileDialog,
    QMessageBox)
from PySide2.QtGui import (
    QKeySequence)
from PySide2.QtCore import (
    QSize)

from .oleview import OleView
from .oledocument import OleDocument
from .stylehelper import dpiScaled


class OleWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("OLE Editor"))
        self.resize(dpiScaled(QSize(880, 510)))

        self._mdiArea = QMdiArea(self)
        self._mdiArea.setViewMode(QMdiArea.TabbedView)
        self._mdiArea.setTabsMovable(True)
        self._mdiArea.setTabsClosable(True)
        self.setCentralWidget(self._mdiArea)

        # seems ugly
        tabbar = self._mdiArea.findChild(QTabBar)
        tabbar.setExpanding(False)

        self._initMenu()

    def _initMenu(self):
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        fileMenu.addAction(self.tr("&Open"),
                           self.onFileMenuOpen,
                           QKeySequence("Ctrl+O"))

    def onFileMenuOpen(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Open OLE Files"),
            filter=self.tr("All Files") + " (*.*)")
        for file in files:
            self.openFile(file)

    def openFile(self, filePath):
        subWin = self.getSubWinByFilePath(filePath)
        if subWin:
            self._mdiArea.setActiveSubWindow(subWin)
            return

        if not OleDocument.isOleFile(filePath):
            QMessageBox.critical(self,
                                self.windowTitle(),
                                self.tr("'{}' is not an OLE2 structed storage file!").format(filePath))
            return

        doc = OleDocument()
        if not doc.open(filePath):
            QMessageBox.critical(self,
                                 self.windowTitle(),
                                 self.tr("Failed to open file: '{}'!").format(filePath))
            return

        view = OleView(doc, self)
        self._mdiArea.addSubWindow(view)

    def getSubWinByFilePath(self, filePath):
        subWindows = self._mdiArea.subWindowList()
        for sw in subWindows:
            if sw.widget().getFilePath() == filePath:
                return sw

        return None
