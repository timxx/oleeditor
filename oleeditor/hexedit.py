# -*- coding: utf-8 -*-

from PySide2.QtWidgets import (
    QAbstractScrollArea)
from PySide2.QtGui import (
    QPainter,
    QFont,
    QFontInfo,
    QFontMetrics,
    QPen)
from PySide2.QtCore import(
    QPointF,
    Qt)

import PySide2


QT_VERSION = (PySide2.__version_info__[0] << 16) + \
    (PySide2.__version_info__[1] << 8) + \
    (PySide2.__version_info__[2])


class HexEdit(QAbstractScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._bytesPerLine = 16
        self._font = self._defaultFont()
        fm = QFontMetrics(self._font)
        self._lineHeight = fm.height()

        if QT_VERSION >= 0x050B00:
            self._charWidth = fm.horizontalAdvance('0')
        else:
            self._charWidth = fm.width('0')
        self._charSpace = self._charWidth // 2

        self._addrWidth = 0
        self._maxWidth = 0
        self._asciiPosX = 0
        self._addrDigit = 4

    def setData(self, data):
        self._data = data

        self._addrDigit = len(str(self.lineCount()))
        if self._addrDigit < 4:
            self._addrDigit = 4
        # + 1 for `h`
        self._addrWidth = (self._addrDigit + 1) * self._charWidth
        hexPos = self._addrWidth + self._charSpace
        hexWidth = self._bytesPerLine * self._charWidth * 2 + \
            (self._bytesPerLine - 1) * self._charSpace
        self._asciiPosX = hexPos + hexWidth + self._charSpace
        asciiWidth = self._bytesPerLine * self._charWidth
        self._maxWidth = self._asciiPosX + asciiWidth

        self._adjustScrollbar()
        self.viewport().update()

    def _defaultFont(self):
        font = QFont("Monospace")
        if self._isFixedPitch(font):
            return font

        font.setStyleHint(QFont.Monospace)
        if self._isFixedPitch(font):
            return font

        font.setStyleHint(QFont.TypeWriter)
        if self._isFixedPitch(font):
            return font

        font.setFamily("Courier")
        return font

    def _isFixedPitch(self, font):
        fontInfo = QFontInfo(font)
        return fontInfo.fixedPitch()

    def _adjustScrollbar(self):
        vScrollBar = self.verticalScrollBar()
        hScrollBar = self.horizontalScrollBar()
        if not self._data:
            vScrollBar.setRange(0, 0)
            hScrollBar.setRange(0, 0)
            return

        hScrollBar.setRange(0, self._maxWidth - self.viewport().width())
        hScrollBar.setPageStep(self.viewport().width())

        linesPerPage = self.linesPerPage()
        totalLines = self.lineCount()

        vScrollBar.setRange(0, totalLines - linesPerPage)
        vScrollBar.setPageStep(linesPerPage)

    def contentOffset(self):
        if not self._data:
            return QPointF(0, 0)

        x = self.horizontalScrollBar().value()
        return QPointF(-x, -0)

    def mapToContents(self, pos):
        x = pos.x() + self.horizontalScrollBar().value()
        y = pos.y() + 0
        return QPoint(x, y)

    def firstVisibleLine(self):
        return self.verticalScrollBar().value()

    def linesPerPage(self):
        return int(self.viewport().height() / self._lineHeight)

    def lineCount(self):
        if not self._data:
            return 0
        return round(len(self._data) / self._bytesPerLine + 0.5)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjustScrollbar()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self.viewport())
        painter.setFont(self._font)

        offset = self.contentOffset()

        startLine = self.firstVisibleLine()
        endLine = startLine + self.linesPerPage() + 1
        endLine = min(self.lineCount(), endLine)

        viewportRect = self.viewport().rect()
        eventRect = event.rect()

        painter.setClipRect(eventRect)

        oldPen = painter.pen()
        painter.setPen(QPen(Qt.gray))
        painter.drawLine(self._addrWidth, 0, self._addrWidth,
                         viewportRect.height())
        xAscii = self._asciiPosX + offset.x()
        xAsciiLine = xAscii - self._charSpace
        painter.drawLine(xAsciiLine, 0, xAsciiLine, viewportRect.height())
        painter.setPen(oldPen)

        xOffset = offset.x() + self._addrWidth + self._charSpace
        x = xOffset
        y = 0
        start = startLine * self._bytesPerLine
        end = min(endLine * self._bytesPerLine, len(self._data))
        lineNum = startLine
        for i in range(start, end):
            if i % self._bytesPerLine == 0:
                y += self._lineHeight
                x = xOffset
                xAscii = self._asciiPosX + offset.x()

                # draw the address
                addr = format(lineNum * self._bytesPerLine,
                              "0%sX" % self._addrDigit) + "h"
                painter.setPen(Qt.gray)
                painter.drawText(self._charSpace, y, addr)
                painter.setPen(oldPen)
                lineNum += 1

            if y > self.viewport().height():
                break

            ch = self._data[i]
            # draw the hex
            oldClip = painter.clipRegion()
            painter.setClipRect(
                self._addrWidth, y - self._lineHeight, viewportRect.width(), self._lineHeight)
            strHex = format(ch, "02X")
            painter.drawText(x, y, strHex)
            x += self._charWidth * 2 + self._charSpace
            painter.setClipRegion(oldClip)

            # draw the ascii
            if ch < 0x20 or ch > 0x126:
                strAscii = "."
            else:
                strAscii = chr(ch)
            painter.drawText(xAscii, y, strAscii)
            xAscii += self._charWidth
