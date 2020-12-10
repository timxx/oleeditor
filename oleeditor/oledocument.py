# -*- coding: utf-8 -*-


class OleDocument:

    def __init__(self):
        self._path = None

    @property
    def path(self):
        return self._path

    def open(self, filePath):
        self._path = filePath

        return True
