# -*- coding: utf-8 -*-


from PySide2.QtWidgets import (
    QMainWindow,
    QMdiArea,
    QTabBar,
    QFileDialog,
    QMessageBox,
    QApplication)
from PySide2.QtGui import (
    QKeySequence,
    QIcon)
from PySide2.QtCore import (
    QSize)

from .oleview import OleView
from .oledocument import OleDocument
from .stylehelper import dpiScaled
from .oleevents import SelectionChangedEvent
from .aboutdialog import AboutDialog


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

        self._mdiArea.subWindowActivated.connect(
            self._onSubWindowActivated)

    def _initMenu(self):
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        ac = fileMenu.addAction(self.tr("&Open"),
                                self.onFileMenuOpen,
                                QKeySequence("Ctrl+O"))
        ac.setIcon(QIcon.fromTheme("document-open"))
        fileMenu.addSeparator()
        ac = fileMenu.addAction(self.tr("&Quit"),
                                self.onFileMenuQuit,
                                QKeySequence("Ctrl+Q"))
        ac.setIcon(QIcon.fromTheme("application-exit"))

        editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        ac = editMenu.addAction(self.tr("&Copy"),
                                self.onEditMenuCopy,
                                QKeySequence("Ctrl+C"))
        ac.setIcon(QIcon.fromTheme("edit-copy"))
        self._acCopy = ac
        self._acCopy.setEnabled(False)

        helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        ac = helpMenu.addAction(self.tr("&About"),
                                self.onHelpMenuAbout)
        ac.setIcon(QIcon.fromTheme("help-about"))
        helpMenu.addAction(self.tr("About &Qt"),
                           QApplication.aboutQt)

    def onFileMenuOpen(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Open OLE Files"),
            filter=self.tr("All Files") + " (*.*)")
        for file in files:
            self.openFile(file)

    def onFileMenuQuit(self):
        self.close()

    def onEditMenuCopy(self):
        curSubWnd = self._mdiArea.activeSubWindow()
        curSubWnd.widget().editor.copy()

    def onHelpMenuAbout(self):
        aboutDialog = AboutDialog(self)
        aboutDialog.exec()

    def _onSubWindowActivated(self, subWin):
        enabled = subWin.widget().editor.hasSelection() if subWin else False
        self._acCopy.setEnabled(enabled)

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

    def event(self, event):
        if event.type() == SelectionChangedEvent.Type:
            curSubWnd = self._mdiArea.activeSubWindow()
            if curSubWnd and curSubWnd.widget() == event.view:
                self._acCopy.setEnabled(event.view.editor.hasSelection())
            return True

        return super().event(event)
