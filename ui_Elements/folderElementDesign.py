import os

from PySide6.QtCore import QObject, QAbstractListModel, Signal
from PySide6.QtGui import QStandardItem, Qt, QStandardItemModel
from PySide6.QtWidgets import QWidget, QPushButton, QListWidget, QGridLayout, QMessageBox, QFileDialog, QListView

from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine, progressDialog
from ui_provider.theme_engine import theme_engine


class UI_folderElement(QWidget):
    # 1. Define the custom signal here at the class level
    onFolderClicked = Signal(list)

    def __init__(self, parent, themeEngine, projectEngine, settingsEngine, signalEngine):
        super().__init__(parent=parent)  # Removed redundant QObject inheritance

        self.themeEngine = themeEngine
        self.projectEngine = projectEngine
        self.settingsEngine = settingsEngine
        self.signalEngine = signalEngine

        # 2. Changed QListWidget to QListView so it can accept a custom model
        self.folderViewList: QListView = QListView(self)

        self.foldersListModel = QStandardItemModel()
        self.folderViewList.setModel(self.foldersListModel)

        # Prevent editing the folder names directly in the list
        self.folderViewList.setEditTriggers(QListView.EditTrigger.NoEditTriggers)

        self.addButton: QPushButton = QPushButton("Add")
        self.removeButton: QPushButton = QPushButton("Remove")
        self.setAcceptDrops(True)
        self._setLayout()
        self._setStyling()

        self._setupConnections()

    def _setLayout(self):
        lyt = QGridLayout()
        lyt.setSpacing(5)
        lyt.setContentsMargins(5, 5, 5, 5)
        lyt.addWidget(self.folderViewList, 0, 0, 1, 2)
        lyt.addWidget(self.addButton, 1, 0, 1, 1)
        lyt.addWidget(self.removeButton, 1, 1, 1, 1)
        self.setLayout(lyt)

    def _setupConnections(self):
        if self.projectEngine:
            self.projectEngine.onProjectLoaded.connect(self.populateFolderList)

        self.folderViewList.clicked.connect(self._handleFolderClick)
        self.removeButton.clicked.connect(self._removeSelectedFolder)
        self.addButton.clicked.connect(self._addFolder)

    def populateFolderList(self):
        self.foldersListModel.clear()
        folders_data = self.projectEngine.getAllFolder()
        for folder in folders_data:
            item = QStandardItem(folder["name"])
            item.setData(folder["path"], Qt.ItemDataRole.UserRole)
            self.foldersListModel.appendRow(item)

    def _gettingImagesFolder(self, folderPath):
        selectedFolder = os.path.abspath(folderPath)
        images = self.projectEngine.getImagesFromFolder(selectedFolder)
        return images

    def _handleFolderClick(self, index):
        folder_path = index.data(Qt.ItemDataRole.UserRole)
        images = self._gettingImagesFolder(folder_path)
        self.onFolderClicked.emit(images)

    def _removeSelectedFolder(self):
        # 4. Fixed typo: folderViewList instead of foldersList
        selected_indexes = self.folderViewList.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        index = selected_indexes[0]
        folder_path = index.data(Qt.ItemDataRole.UserRole)
        folder_name = index.data(Qt.ItemDataRole.DisplayRole)  # Safer way to get the display text

        confirmation = QMessageBox.question(
            self,
            "Remove Folder",
            f"Are you sure you want to remove '{folder_name}'?",
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return
        print(f"this is path :  {folder_path}")
        self.projectEngine.removeFolder(folder_path)
        self.foldersListModel.removeRow(index.row())

    def _addFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select a Folder for Images")

        if not folder_path:
            return

        for row in range(self.foldersListModel.rowCount()):
            index = self.foldersListModel.index(row, 0)
            if index.data(Qt.ItemDataRole.UserRole) == folder_path:
                return
        progressBar = progressDialog()
        progressBar.setLabelText(f"adding {os.path.basename(folder_path)} to Project")
        progressBar.show()
        self.projectEngine.addFolder(folder_path)
        progressBar.destroy()

        folder_name = os.path.basename(folder_path)
        item = QStandardItem(folder_name)
        item.setData(folder_path, Qt.ItemDataRole.UserRole)
        self.foldersListModel.appendRow(item)

    def _setStyling(self):
        btnStyle = f"""
                        QPushButton{{
                        background-color:{self.themeEngine.get("accent_primary")};
                        color:{self.themeEngine.get("text")};
                        font:{self.themeEngine.getFont("button")};
                        border-radius:{self.themeEngine.getProperty("border_radius_sm")}
                        }}
    
                        QPushButton:hover{{
                        background-color:{self.themeEngine.get("accent_hover")};
    
                        }}
                                """
        self.addButton.setFixedHeight(24)
        self.removeButton.setFixedHeight(24)
        self.addButton.setStyleSheet(btnStyle)
        self.removeButton.setStyleSheet(btnStyle)

        self.setStyleSheet(f"""
                                background-color:{self.themeEngine.get("primary")};
                                """)

        self.folderViewList.setStyleSheet(f"""
                                        background-color:{self.themeEngine.get("secondary")}; 
                                        color:{self.themeEngine.get("text")};
                                        font:{self.themeEngine.getFont("body")}
                                                """)

    def dragEnterEvent(self, event):
        # Check if the dragged item contains file paths (URLs)
        if event.mimeData().hasUrls():
            # Verify that at least one of the dragged items is a directory, not a file
            for url in event.mimeData().urls():
                if url.isLocalFile() and os.path.isdir(url.toLocalFile()):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # Loop through all dropped items (supports dropping multiple folders at once!)
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    folder_path = url.toLocalFile()
                    # Only process it if it's an actual directory
                    if os.path.isdir(folder_path):
                        self._processNewFolder(folder_path)
            event.acceptProposedAction()

    def _processNewFolder(self, folder_path):
        # This new method handles the actual database and UI insertion
        # It can be called by both the Add button AND the Drop event

        # Prevent duplicates
        for row in range(self.foldersListModel.rowCount()):
            index = self.foldersListModel.index(row, 0)
            if index.data(Qt.ItemDataRole.UserRole) == folder_path:
                return

        progressBar = progressDialog()
        progressBar.setLabelText(f"Adding {os.path.basename(folder_path)} to Project")
        progressBar.show()

        self.projectEngine.addFolder(folder_path)

        progressBar.destroy()

        folder_name = os.path.basename(folder_path)
        item = QStandardItem(folder_name)
        item.setData(folder_path, Qt.ItemDataRole.UserRole)
        self.foldersListModel.appendRow(item)
