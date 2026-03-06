import datetime
import os.path
import time

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt, QAbstractTableModel, QAbstractListModel, QModelIndex,
                            QStandardPaths)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
                               QLabel, QLineEdit, QListView, QPushButton,
                               QSizePolicy, QToolButton, QWidget, QFileDialog)

from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine


class recentProjectsViewModel(QAbstractListModel):
    def __init__(self, themeEngine, projectEngine, settingsEngine, signalEngine):
        super().__init__()
        self.themeEngine = themeEngine
        self.projectEngine = projectEngine
        self.settingsEngine = settingsEngine
        self.signalEngine = signalEngine

        # 1. Fetch the raw dictionary from settings
        raw_projects = self.settingsEngine.get("recentProjects")

        # 2. Convert the dictionary into a list so we can access it by row index
        if raw_projects:
            self.project_list = list(raw_projects.values())
        else:
            self.project_list = []

        print(f"Loaded {len(self.project_list)} projects")

    def rowCount(self, parent=QModelIndex()):
        # Return the length of our new list
        return len(self.project_list)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Always check if the index is valid
        if not index.isValid():
            return None

        # Ensure the row requested is within our data bounds
        if 0 <= index.row() < self.rowCount():
            project = self.project_list[index.row()]

            # The DisplayRole is what the ListView asks for when it wants text to show
            if role == Qt.ItemDataRole.DisplayRole:

                return os.path.basename(project.get("projectFile"))

            elif role == Qt.ItemDataRole.ToolTipRole:
                return f"""Created: {project.get('dateCreated', 'Unknown date')}\nClient Name: {project.get('clientName', 'Not Available')}"""

        return None


class UI_projectsPage(QWidget, object):
    def __init__(self, themeEngine, projectEngine,
                 settingsEngine, signalEngine):
        super().__init__()

        self.themeEngine: theme_engine = themeEngine
        self.projectEngine: project_engine = projectEngine
        self.settingsEngine: settings_engine = settingsEngine
        self.signalEngine: signals_engine = signalEngine

        self.recentProjectsView = QListView(self)
        self.recentProjectsView.setMinimumSize(QSize(400, 0))

        self.recentProjectLabel = QLabel(self)

        self.createFrame = QFrame(self)
        self.createFrame.setMinimumSize(QSize(300, 0))
        self.createFrame.setMaximumSize(QSize(500, 16777215))
        self.createFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.createFrame.setFrameShadow(QFrame.Shadow.Raised)

        self.createProjectLabel = QLabel(self.createFrame)

        self.createProjectLabel.setMaximumSize(QSize(16777215, 21))

        self.projectNameLabel = QLabel(self.createFrame)

        self.projectLocationLabel = QLabel(self.createFrame)

        self.projectLocationEntry = QLineEdit(self.createFrame)
        self.selectProjectLocationButton = QToolButton(self.createFrame)

        self.UseDefauldProjectLocationCheckBox = QCheckBox(self.createFrame)

        self.createProjectButton = QPushButton(self.createFrame)
        self.createProjectButton.setMinimumSize(QSize(0, 40))
        self.projectNameEntry = QLineEdit(self.createFrame)
        self.projectNameEntry.setFixedHeight(25)
        self.projectLocationEntry.setFixedHeight(25)

        self.setupLayou()
        self.styling()
        self.setupModel()
        self._setupConnections()

        self.recentProjectLabel.setText(u"Recent Project")
        self.createProjectLabel.setText(u"Create Project")
        self.projectNameLabel.setText(u"Name :")
        self.projectLocationLabel.setText(u"Location :")
        self.selectProjectLocationButton.setText("...")
        self.UseDefauldProjectLocationCheckBox.setText(u"Use Default Location")
        self.createProjectButton.setText(u"Create Project")

    def setupModel(self):
        self.recentProjectsView.setViewMode(QListView.ViewMode.IconMode)
        self.recentProjectsView.setResizeMode(QListView.ResizeMode.Adjust)
        self.recentProjectsView.setSpacing(10)
        self.recentProjectsViewModel = recentProjectsViewModel(themeEngine=self.themeEngine,
                                                               projectEngine=self.projectEngine,
                                                               settingsEngine=self.settingsEngine,
                                                               signalEngine=self.signalEngine)
        self.recentProjectsView.setModel(self.recentProjectsViewModel)

    def setupLayou(self):
        pgLayout = QGridLayout(self)
        pgLayout.setSpacing(10)
        pgLayout.setContentsMargins(10, 10, 10, 10)
        pgLayout.addWidget(self.recentProjectLabel, 0, 0, 1, 1)
        pgLayout.addWidget(self.recentProjectsView, 1, 0, 1, 1)

        self.createFrameLayout = QGridLayout(self.createFrame)
        self.createFrameLayout.setHorizontalSpacing(6)
        self.createFrameLayout.setVerticalSpacing(10)
        self.createFrameLayout.setContentsMargins(15, 10, 10, 10)

        self.createFrameLayout.addWidget(self.createProjectLabel, 0, 0, 1, 3)
        self.createFrameLayout.addWidget(self.projectNameLabel, 1, 0, 1, 1)
        self.createFrameLayout.addWidget(self.projectLocationLabel, 2, 0, 1, 1)
        self.createFrameLayout.addWidget(self.projectLocationEntry, 2, 1, 1, 1)
        self.createFrameLayout.addWidget(self.selectProjectLocationButton, 2, 2, 1, 1)
        self.createFrameLayout.addWidget(self.UseDefauldProjectLocationCheckBox, 3, 0, 1, 3)
        self.createFrameLayout.addWidget(self.createProjectButton, 4, 0, 1, 3, Qt.AlignmentFlag.AlignBottom)
        self.createFrameLayout.addWidget(self.projectNameEntry, 1, 1, 1, 2)
        pgLayout.addWidget(self.createFrame, 0, 1, 2, 1)

    def styling(self):
        self.setStyleSheet(f"""
                                              """)
        self.recentProjectLabel.setStyleSheet(f"""
        color: {self.themeEngine.get("text")};
        font: {self.themeEngine.getFont("hd_line")};
        border: 0px;
        """)

        self.recentProjectsView.setStyleSheet(f"""
                
                color: {self.themeEngine.get("text")};
                background-color: {self.themeEngine.get("secondary")};
                font: {self.themeEngine.getFont("body")};
                border-radius: {self.themeEngine.getProperty("border_radius_lg")}px;
                border: 0px
                """)
        self.createFrame.setStyleSheet(f"""
                background-color: {self.themeEngine.get("secondary")};
                border: 0px;
                border-radius: {self.themeEngine.getProperty("border_radius_lg")}px;
        
                """)
        self.createProjectLabel.setStyleSheet(f"""
                font: {self.themeEngine.getFont("hd_line")};
                color: {self.themeEngine.get("text")};
                border: 0px;
                """)
        self.projectNameLabel.setStyleSheet(f"""
                font: {self.themeEngine.getFont("body")};
                color: {self.themeEngine.get("text")};
                """)
        self.projectLocationLabel.setStyleSheet(f"""
                font: {self.themeEngine.getFont("body")};
                color: {self.themeEngine.get("text")};
                """)
        self.UseDefauldProjectLocationCheckBox.setStyleSheet(f"""
                font: {self.themeEngine.getFont("body")};
                color: {self.themeEngine.get("text")};
                """)
        self.createProjectButton.setStyleSheet(f"""
                QPushButton
                {{
                background-color: {self.themeEngine.get("accent_primary")};
                color: {self.themeEngine.get("text")};
                font: {self.themeEngine.getFont("large_button")};
                border-radius: {self.themeEngine.getProperty("border_radius_sm")}
                }}
        
                QPushButton: hover
                {{
                    background-color: {self.themeEngine.get("accent_hover")};
                }}
                """)
        self.projectNameEntry.setStyleSheet(f"""
                background-color: {self.themeEngine.get("primary")};
                border: 1px solid {self.themeEngine.get("accent_primary")};
                border-radius: {self.themeEngine.getProperty("border_radius_sm")}px;
                font: {self.themeEngine.getFont("body")};
                color: {self.themeEngine.get("text")};
                """)
        self.projectLocationEntry.setStyleSheet(f"""
                background-color: {self.themeEngine.get("primary")};
                border: 1px solid {self.themeEngine.get("accent_primary")};
                border-radius: {self.themeEngine.getProperty("border_radius_sm")}px;
                font: {self.themeEngine.getFont("body")};
                color: {self.themeEngine.get("text")};
                """)
        self.selectProjectLocationButton.setStyleSheet(f"""
                QToolButton
                {{
                    background-color: {self.themeEngine.get("accent_primary")};
                color: {self.themeEngine.get("text")};
                font: {self.themeEngine.getFont("button")};
                font-weight: 1000;
                border-radius: {self.themeEngine.getProperty("border_radius_sm")}
                }}
        
                QToolButton: hover
                {{
                    background-color: {self.themeEngine.get("accent_hover")};
                }}
                """)

    def _setupConnections(self):
        self.createProjectButton.clicked.connect(self.CreateProject)
        self.recentProjectsView.doubleClicked.connect(self.loadRecentProject)
        self.selectProjectLocationButton.clicked.connect(self.__selectNewProjectLocation)
        self.UseDefauldProjectLocationCheckBox.clicked.connect(self.defaultLocationCheckBoxChanged)

    def defaultLocationCheckBoxChanged(self):
        if self.UseDefauldProjectLocationCheckBox.isChecked():
            default_path = self.settingsEngine.get("defaultProjectSaveLocation")
            if default_path == None or not os.path.exists(default_path):
                default_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            self.projectLocationEntry.setText(default_path)
            self.projectLocationEntry.setDisabled(True)
            print("Using default location")
        else:
            self.projectLocationEntry.setDisabled(False)
            print("Custom location enabled")

    def __selectNewProjectLocation(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Please select a folder where you want to store Project File"
        )

        if folder:
            self.projectLocationEntry.setText(folder)

    def CreateProject(self):
        projectName = self.projectNameEntry.text()
        projectLocation = self.projectLocationEntry.text()

        if not projectName:
            print("please enter a project name")
            return

        if not os.path.exists(projectLocation):
            print("please select A valid Location to save the project")
            return

        projectFilePath = os.path.join(projectLocation, projectName)
        self.projectEngine.load(projectFilePath)

        oldRecentProjectsData = self.settingsEngine.get("recentProjects") or {}

        currentDate = datetime.datetime.now().strftime("%d/%m/%Y")

        # Remove if already exists (prevents duplicates)
        if projectName in oldRecentProjectsData:
            del oldRecentProjectsData[projectName]

        # Add project at top
        newRecentProjects = {
            projectName: {
                "projectFile": projectFilePath,
                "dateCreated": currentDate
            }
        }

        # Merge new project first (so it's most recent)
        updatedRecentProjects = {**newRecentProjects, **oldRecentProjectsData}

        # Optional: limit to last 10 projects
        updatedRecentProjects = dict(list(updatedRecentProjects.items())[:10])

        self.settingsEngine.set("recentProjects", updatedRecentProjects)

    def loadRecentProject(self, index):
        row = index.row()
        project_path, dateCreated = self.recentProjectsViewModel.project_list[row].values()
        self.projectEngine.load(project_path)
