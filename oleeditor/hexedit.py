# -*- coding: utf-8 -*-

from PySide2.QtWidgets import (
    QAbstractScrollArea,
    QApplication)
from PySide2.QtGui import (
    QPainter,
    QFont,
    QFontInfo,
    QFontMetrics,
    QPen,
    QColor)
from PySide2.QtCore import(
    QPointF,
    QPoint,
    Qt,
    QRect,
    QTimer,
    Signal)

import PySide2

from .stylehelper import dpiScaled


QT_VERSION = (PySide2.__version_info__[0] << 16) + \
    (PySide2.__version_info__[1] << 8) + \
    (PySide2.__version_info__[2])


class TextCursor():

    def __init__(self):
        self.clear()

    def clear(self):
        self._beginLine = -1
        self._beginPos = -1
        self._endLine = -1
        self._endPos = -1
        self._inAsciiView = False

    def isValid(self):
        return self._beginLine != -1 and \
            self._endLine != -1 and \
            self._beginPos != -1 and \
            self._endPos != -1

    def hasMultiLines(self):
        if not self.isValid():
            return False

        return self._beginLine != self._endLine

    def hasSelection(self):
        if not self.isValid():
            return False

        if self.hasMultiLines():
            return True
        return self._beginPos != self._endPos

    def within(self, line):
        if not self.hasSelection():
            return False

        if line >= self.beginLine() and line <= self.endLine():
            return True

        return False

    def beginLine(self):
        return min(self._beginLine, self._endLine)

    def endLine(self):
        return max(self._beginLine, self._endLine)

    def beginPos(self):
        if self._beginLine == self._endLine:
            return min(self._beginPos, self._endPos)
        elif self._beginLine < self._endLine:
            return self._beginPos
        else:
            return self._endPos

    def endPos(self):
        if self._beginLine == self._endLine:
            return max(self._beginPos, self._endPos)
        elif self._beginLine < self._endLine:
            return self._endPos
        else:
            return self._beginPos

    def moveTo(self, line, pos):
        self._beginLine = line
        self._beginPos = pos
        self._endLine = line
        self._endPos = pos

    def selectTo(self, line, pos):
        self._endLine = line
        self._endPos = pos

    def moveToAsciiView(self):
        self._inAsciiView = True

    def moveToHexView(self):
        self._inAsciiView = False

    def inAsciiView(self):
        return self._inAsciiView

    def inHexView(self):
        return not self._inAsciiView


class HexEdit(QAbstractScrollArea):

    selectionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._bytesPerLine = 16
        self._charsPerLine = self._bytesPerLine * 2 + (self._bytesPerLine - 1)
        self._font = self._defaultFont()
        fm = QFontMetrics(self._font)
        self._lineHeight = fm.height()
        self._ascent = fm.ascent()

        if QT_VERSION >= 0x050B00:
            self._charWidth = fm.horizontalAdvance('0')
        else:
            self._charWidth = fm.width('0')

        self._addrWidth = 0
        self._hexPosX = 0
        self._asciiPosX = 0
        self._addrDigit = 4
        self._maxWidth = 0

        self._cursor = TextCursor()
        self._blink = False
        self._cursorTimer = QTimer(self)
        # qApp.cursorFlashTime() is too slow..
        self._cursorTimer.setInterval(500)
        self._cursorTimer.timeout.connect(self.blinkCursor)

    def setData(self, data):
        self._data = data

        self._addrDigit = len(str(self.lineCount()))
        if self._addrDigit < 4:
            self._addrDigit = 4
        # + 1 for `h`
        self._addrWidth = (self._addrDigit + 1) * self._charWidth
        self._hexPosX = self._addrWidth + self._charWidth
        hexWidth = self._bytesPerLine * self._charWidth * 2 + \
            (self._bytesPerLine - 1) * self._charWidth
        self._asciiPosX = self._hexPosX + hexWidth + self._charWidth
        asciiWidth = self._bytesPerLine * self._charWidth
        self._maxWidth = self._asciiPosX + asciiWidth

        self._cursor.moveTo(0, 0)
        if self.hasFocus():
            self._cursorTimer.start()
        else:
            self._blink = True

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
        c = len(self._data) // self._bytesPerLine
        if len(self._data) % self._bytesPerLine != 0:
            c += 1
        return c

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

        if eventRect == self._cursorRect():
            self._drawCursor(painter, startLine, endLine)
            return

        oldPen = painter.pen()
        painter.setPen(QPen(Qt.gray))

        spaceWidth = self._charWidth // 2
        painter.drawLine(self._addrWidth + spaceWidth, 0,
                         self._addrWidth + spaceWidth, viewportRect.height())
        xAscii = self._asciiPosX + offset.x()
        xAsciiLine = xAscii - spaceWidth
        painter.drawLine(xAsciiLine, 0, xAsciiLine, viewportRect.height())
        painter.setPen(oldPen)

        self._drawSelection(painter, startLine, endLine)

        x = offset.x() + self._hexPosX
        y = self._ascent
        start = startLine * self._bytesPerLine
        end = min(endLine * self._bytesPerLine, len(self._data))
        lineNum = startLine

        self._drawAddress(painter, spaceWidth, y, lineNum)
        activeLine = -1
        if self._cursor.isValid() and not self._cursor.hasSelection():
            activeLine = self._cursor.beginLine()

        for i in range(start, end):
            if i != start and i % self._bytesPerLine == 0:
                y += self._lineHeight
                x = offset.x() + self._hexPosX
                xAscii = self._asciiPosX + offset.x()
                lineNum += 1
                self._drawAddress(painter, spaceWidth, y, lineNum)

            if y > self.viewport().height():
                break

            ch = self._data[i]
            # draw the hex
            oldClip = painter.clipRegion()
            if activeLine == lineNum:
                painter.setPen(Qt.red)

            painter.setClipRect(self._hexPosX, y - self._lineHeight,
                                viewportRect.width(), self._lineHeight)
            strHex = format(ch, "02X")
            painter.drawText(x, y, strHex)
            x += self._charWidth * 3
            painter.setClipRegion(oldClip)

            # draw the ascii
            if ch < 0x20 or ch > 0x126:
                strAscii = "."
            else:
                strAscii = chr(ch)
            painter.drawText(xAscii, y, strAscii)
            xAscii += self._charWidth

            if activeLine == lineNum:
                painter.setPen(oldPen)

        self._drawCursor(painter, startLine, endLine)

    def _drawAddress(self, painter, x, y, lineNum):
        addr = format(lineNum * self._bytesPerLine,
                      "0%sX" % self._addrDigit) + "h"
        oldPen = painter.pen()
        painter.setPen(Qt.gray)
        painter.drawText(x, y, addr)
        painter.setPen(oldPen)

    def _drawSelection(self, painter, startLine, endLine):
        if not self._cursor.hasSelection():
            return

        beginRow = self._cursor.beginLine()
        endRow = self._cursor.endLine()

        if beginRow > endLine:
            return
        if endRow < startLine:
            return

        brush = QColor(173, 214, 255)
        beginCol = self._cursor.beginPos()
        endCol = self._cursor.endPos()

        def _calcX(col, forHex):
            if forHex:
                return col * self._charWidth
            return (col + 1) // 3 * self._charWidth

        def _calcWidth(col, forHex):
            if forHex:
                return col * self._charWidth
            return (col + 1) // 3 * self._charWidth

        oldClip = painter.clipRegion()
        rc = self.viewport().rect()
        painter.setClipRect(self._hexPosX, 0, rc.width(), rc.height())
        if self._cursor.hasMultiLines():
            def _doDraw(xOffset, forHex):
                # first line
                x = xOffset + _calcX(beginCol, forHex)
                w = _calcWidth(self._charsPerLine - beginCol, forHex)
                y = (beginRow - self.firstVisibleLine()) * self._lineHeight
                h = self._lineHeight
                painter.fillRect(x, y, w, h, brush)

                # middle lines
                if (endRow - 1) > beginRow:
                    x = xOffset
                    y += self._lineHeight
                    w = _calcWidth(self._charsPerLine, forHex)
                    h = (endRow - 1 - beginRow) * self._lineHeight
                    painter.fillRect(x, y, w, h, brush)

                # last line
                x = xOffset
                y = (endRow - self.firstVisibleLine()) * self._lineHeight
                w = _calcWidth(endCol, forHex)
                h = self._lineHeight
                painter.fillRect(x, y, w, h, brush)

            xOffset = self.contentOffset().x()
            _doDraw(self._hexPosX + xOffset, True)
            _doDraw(self._asciiPosX + xOffset, False)
        else:
            def _doDraw(xOffset, forHex):
                x = xOffset + _calcX(beginCol, forHex)
                y = (beginRow - self.firstVisibleLine()) * self._lineHeight
                w = _calcWidth(endCol - beginCol, forHex)
                h = self._lineHeight
                painter.fillRect(x, y, w, h, brush)

            xOffset = self.contentOffset().x()
            _doDraw(self._hexPosX + xOffset, True)
            _doDraw(self._asciiPosX + xOffset, False)

        painter.setClipRegion(oldClip)

    def _drawCursor(self, painter, startLine, endLine):
        if self._cursor.hasSelection():
            return
        if not self._cursor.isValid():
            return
        if self._blink:
            return

        row = self._cursor.beginLine()
        if row < startLine or row > endLine:
            return

        rect = self._cursorRect()
        painter.fillRect(rect, Qt.black)

    def _cursorRect(self):
        if self._cursor.hasSelection() or not self._cursor.isValid():
            return QRect()

        row = self._cursor.beginLine()
        pos = self._cursor.beginPos()
        xOffset = self.contentOffset().x()
        if self._cursor.inHexView():
            x = self._hexPosX + xOffset + pos * self._charWidth
        else:
            x = self._asciiPosX + xOffset + (pos + 1) // 3 * self._charWidth
        x -= dpiScaled(1)
        y = (row - self.firstVisibleLine()) * self._lineHeight

        return QRect(x, y, dpiScaled(1), self._lineHeight)

    def rowColForPos(self, pos, inAsciiView):
        y = max(0, pos.y())
        r = int(y / self._lineHeight)
        r += self.firstVisibleLine()

        rows = self.lineCount()
        if r >= rows:
            r = rows - 1

        halfChar = self._charWidth // 2
        if inAsciiView:
            c = (pos.x() + halfChar - self._asciiPosX) // self._charWidth
            # same as hex view
            c = 3 * c - 1
        else:
            c = (pos.x() + halfChar - self._hexPosX) // self._charWidth

        if r == rows - 1:
            rest = len(self._data) % self._bytesPerLine
            if rest != 0:
                c = min(c, rest * 3)
        c = max(0, min(c, self._charsPerLine))

        return r, c

    def _invalidateSelection(self):
        if not self._cursor.hasSelection() and \
                not self._cursor.isValid():
            return

        begin = self._cursor.beginLine()
        end = self._cursor.endLine()

        x = 0
        y = (begin - self.firstVisibleLine()) * self._lineHeight
        w = self.viewport().width()
        h = (end - begin + 1) * self._lineHeight

        rect = QRect(x, y, w, h)
        # offset for some odd fonts LoL
        offset = int(self._lineHeight / 2)
        rect.adjust(0, -offset, 0, offset)
        self.viewport().update(rect)

    def mousePressEvent(self, event):
        if not self._data:
            return

        if event.button() != Qt.LeftButton:
            return

        self._invalidateSelection()

        pos = self.mapToContents(event.pos())
        inAsciiView = pos.x() >= self._asciiPosX
        r, c = self.rowColForPos(pos, inAsciiView)
        # not allow edit on hex end
        if not inAsciiView and c % 3 == 2:
            c -= 2
        self._cursor.moveTo(r, c)
        if pos.x() >= self._asciiPosX:
            self._cursor.moveToAsciiView()
        elif pos.x() >= self._hexPosX:
            self._cursor.moveToHexView()

        self._cursorTimer.start()
        self._invalidateSelection()

        self.selectionChanged.emit()

    def mouseMoveEvent(self, event):
        if not self._data:
            return

        if event.buttons() != Qt.LeftButton:
            return

        self._invalidateSelection()
        pos = self.mapToContents(event.pos())
        r, c = self.rowColForPos(pos, self._cursor.inAsciiView())
        self._cursor.selectTo(r, c)

        if self._cursor.inHexView() and self._cursor.hasSelection():
            beginCol = self._cursor.beginPos()
            endCol = self._cursor.endPos()
            # select one byte at least
            if beginCol % 3 == 1:
                beginCol -= 1
            if endCol % 3 == 1 and (endCol + 1) <= self._charsPerLine:
                endCol += 1
            # do not select the space
            if beginCol % 3 == 2 and (beginCol + 1) <= self._charsPerLine:
                beginCol += 1
            if endCol % 3 == 0 and endCol > 0:
                endCol -= 1
            if r == self._cursor.endLine():
                self._cursor.moveTo(self._cursor.beginLine(), beginCol)
                self._cursor.selectTo(r, endCol)
            else:
                self._cursor.moveTo(self._cursor.endLine(), endCol)
                self._cursor.selectTo(r, beginCol)

        if self._cursor.hasMultiLines():
            # select at least one char
            if c == 0 and self._cursor.endLine() == r:
                self._cursor.selectTo(r, c + 2)
            elif c == self._charsPerLine and self._cursor.beginLine() == r:
                self._cursor.selectTo(r, c - 2)

        self._invalidateSelection()
        self.selectionChanged.emit()

    def blinkCursor(self):
        rc = self._cursorRect()
        if rc.isValid():
            self._blink = not self._blink
            self.viewport().update(rc)

    def focusInEvent(self, event):
        rc = self._cursorRect()
        if rc.isValid():
            self._cursorTimer.start()

    def focusOutEvent(self, event):
        self._cursorTimer.stop()

    def copy(self):
        if self._cursor.inHexView():
            self.copyAsHex()
        else:
            self.copyAsText()

    def copyAsHex(self):
        self._doCopy(True)

    def copyAsText(self):
        self._doCopy(False)

    def _doCopy(self, asHex):
        if not self._data or not self._cursor.hasSelection():
            return

        begin = (self._cursor.beginPos() + 1) // 3
        end = (self._cursor.endPos() + 1) // 3
        begin += self._cursor.beginLine() * self._bytesPerLine
        end += self._cursor.endLine() * self._bytesPerLine
        data = self._data[begin: end]

        clipboard = QApplication.clipboard()
        text = ""
        if asHex:
            for i in range(len(data)):
                if (i + 1) != len(data):
                    text += format(data[i], "02X") + " "
                else:
                    text += format(data[i], "02X")
        else:
            # TODO: detect encoding?
            for ch in data:
                if ch < 0x20 or ch > 0x126:
                    text += "."
                else:
                    text += chr(ch)
        clipboard.setText(text)

    def hasSelection(self):
        return self._cursor.hasSelection()
