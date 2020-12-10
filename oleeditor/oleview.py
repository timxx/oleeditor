# -*- coding: utf-8 -*-

from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QFileIconProvider)
from PySide2.QtCore import (
    QFileInfo,
    Qt)

from .hexedit import HexEdit


class OleView(QWidget):
    OleTypeRole = Qt.UserRole + 1
    OleFolderType = 1
    OleFileType = 2

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
        self._splitter.setStretchFactor(0, 2)
        self._splitter.setStretchFactor(1, 7)

        self._folderIcon = None
        self._fileIcon = None
        self._initOleTree()

        self._oleTree.expandAll()

    def getFilePath(self):
        return self._doc.path

    def _initOleTree(self):
        entries = self._doc.getFileEntries()
        if not entries:
            return

        if not self._folderIcon:
            icon = QFileIconProvider()
            self._folderIcon = icon.icon(QFileIconProvider.Folder)
            self._fileIcon = icon.icon(QFileIconProvider.File)

        root = QTreeWidgetItem()
        root.setText(0, self.tr("OLE Root Entry"))
        root.setIcon(0, self._folderIcon)
        root.setData(0, OleView.OleTypeRole, OleView.OleFolderType)
        self._oleTree.addTopLevelItem(root)

        for entry in entries:
            parentItem = root
            path = root.text(0)
            for i in range(len(entry)):
                item = QTreeWidgetItem()
                item.setText(0, entry[i])

                if (i + 1) == len(entry):
                    item.setIcon(0, self._fileIcon)
                    item.setData(0, OleView.OleTypeRole, OleView.OleFolderType)
                    parentItem.addChild(item)
                    break

                path += "/" + entry[i]
                found = False
                items = self._oleTree.findItems(entry[i], Qt.MatchExactly | Qt.MatchRecursive)
                for i in items:
                    if i.data(0, OleView.OleTypeRole) != OleView.OleFolderType:
                        continue
                    if path == self._makeFullPath(i.text(0), i.parent()):
                        found = True
                        parentItem = i
                        break

                if not found:
                    item.setIcon(0, self._folderIcon)
                    item.setData(0, OleView.OleTypeRole, OleView.OleFolderType)
                    parentItem.addChild(item)
                    parentItem = item

    def _makeFullPath(self, path, parent):
        full_path = path
        while parent != None:
            full_path = parent.text(0) + "/" + full_path
            parent = parent.parent()

        return full_path
