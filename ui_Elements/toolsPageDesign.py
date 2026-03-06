import os.path

from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex
from PySide6.QtWidgets import QFrame, QWidget, QStackedWidget, QHBoxLayout, QComboBox, QGridLayout, QListView

from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine


class photosViewModel(QAbstractListModel):
    def __init__(self, images=None):
        super().__init__()
        self.images = images or []

    def rowCount(self, parent=QModelIndex()):
        return len(self.images)

    def data(self, index, role):
        if not index.isValid(): return None
        row = index.row()
        image = self.images[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return os.path.basename(image)
        if role == Qt.ItemDataRole.ToolTipRole:
            return "Location : {image}"
        if role == Qt.ItemDataRole.DecorationRole:
            return thumb_engine.getThumb(self.image, self.size, False)


class templatesPageDesign(QFrame):
    def __init__(self, parent, themeEngine: theme_engine, projectEngine: project_engine,
                 settingsEngine: settings_engine, signalEngine: signals_engine):
        super().__init__(parent)

        self.themeEngine = themeEngine
        self.projectEngine = projectEngine
        self.settingsEngine = settingsEngine
        self.signalEngine = signalEngine

        self.sizeSelectionBox = QComboBox(self)
        self.templatesView = QListView(self)

        self.sizeSelectionBox.setFixedHeight(25)

        lyt = QGridLayout(self)
        lyt.setSpacing(5)
        lyt.setContentsMargins(5, 5, 5, 5)

        lyt.addWidget(self.sizeSelectionBox, 0, 0, 1, 1)
        lyt.addWidget(self.templatesView, 1, 0, 1, 1)
        self._populate()
        self.setupStyling()

    def _populate(self):
        self.sizeSelectionBox.addItems(self.settingsEngine.get("sheetSizesAvailable"))
        self.sizeSelectionBox.setCurrentText(self.settingsEngine.get("sheetSizeSelected"))

        self.sizeSelectionBox.currentTextChanged.connect(
            lambda: self.settingsEngine.set("sheetSizeSelected", self.sizeSelectionBox.currentText()))

    def setupStyling(self):
        dropDownStyle = f"""
                    QComboBox {{
                        background-color: {self.themeEngine.get("secondary")};
                        color: #ffffff;
                        border: 1px solid {self.themeEngine.get("accent_primary")};
                        border-radius: {self.themeEngine.getProperty("border_radius_sm")}px;
                        padding: 4px 10px;
                        font: {self.themeEngine.getFont("body")};
                    }}
                    
                    QComboBox:hover {{
                        border: 1px solid {self.themeEngine.get("accent_hover")};
                    }}
                    
                    QComboBox:focus {{
                        border: 2px solid {self.themeEngine.get("accent_primary")};
                    }}
                    
                    QComboBox::drop-down {{
                        border: none;
                        width: 20px;
                    }}
                    
                    QComboBox::down-arrow {{
                        image: none;
                    }}
                    
                    QComboBox QAbstractItemView {{
                        background-color: {self.themeEngine.get("secondary")};
                        color: white;
                        border: 1px solid {self.themeEngine.get("accent_primary")};
                        outline: none;
                        padding: 1px;
                    }}
                    
                    QComboBox QAbstractItemView::item {{
                        padding: 0px;
                        color: white;
                    }}
                    
                    QComboBox QAbstractItemView::item:hover {{
                        background-color: {self.themeEngine.get("accent_hover")};
                        color: white;
                    }}
                    
                    QComboBox QAbstractItemView::item:selected {{
                        background-color: {self.themeEngine.get("accent_primary")};
                        color: white;
                    }}
                                                            """
        self.sizeSelectionBox.setStyleSheet(dropDownStyle)

    def setupTemplateViewModel(self): ...


class toolsPageDesign(QFrame):
    def __init__(self, parent, themeEngine, projectEngine,
                 settingsEngine, signalEngine):
        super().__init__(parent=parent)
        self.themeEngine = themeEngine
        self.projectEngine = projectEngine
        self.settingsEngine = settingsEngine
        self.signalEngine = signalEngine

        self.navBar = QFrame(self)
        self.navBar.setFixedWidth(30)
        self.toolsPages = QStackedWidget(self)
        lyt = QHBoxLayout()

        lyt.addWidget(self.toolsPages)
        lyt.addWidget(self.navBar)
        self.setLayout(lyt)

        self._pageLinking()
        self.setupConnections()
        self._setupStyling()

    def _pageLinking(self):
        self.templatesPage = templatesPageDesign(self, themeEngine=self.themeEngine, projectEngine=self.projectEngine,
                                                 settingsEngine=self.settingsEngine, signalEngine=self.signalEngine)
        self.toolsPages.addWidget(self.templatesPage)

    def setupConnections(self): pass

    def _setupStyling(self):
        self.toolsPages.setStyleSheet("border: 0px solid black;")
