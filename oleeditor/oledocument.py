# -*- coding: utf-8 -*-

from olefile import olefile


class OleDocument:

    def __init__(self):
        self._path = None
        self._doc = None

    @property
    def path(self):
        return self._path

    def open(self, filePath):
        try:
            self._doc = olefile.OleFileIO(filePath)
        except:
            return False
        self._path = filePath

        return True

    @staticmethod
    def isOleFile(filePath):
        return olefile.isOleFile(filePath)

    def getFileEntries(self):
        return self._doc.listdir(streams=True, storages=False)

    def getStreamData(self, path):
        with self._doc.openstream(path) as f:
            return f.read()
        return None
