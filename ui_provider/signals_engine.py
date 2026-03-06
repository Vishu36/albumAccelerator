from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QProgressDialog


class progressDialog(QProgressDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Album Accelerator Processing...")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setCancelButton(None)
        self.setMinimumDuration(0)  # Forces the dialog to show immediately


class signals_engine(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.projectLoaded = Signal()
        self.projectCreated = Signal()

        self.imageFolderClicked = Signal()
        self.imageFolderNameChanged = Signal()
        self.imageFolderAdded = Signal()
        self.imageFolderRemoved = Signal()


