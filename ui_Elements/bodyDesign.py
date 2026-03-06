from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QFrame, QStackedWidget, QPushButton, QGridLayout, QHBoxLayout

from ui_Elements.projectsPageDesign import UI_projectsPage
from ui_Elements.semiAutoPageDesign import UI_semiAutoPage
from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine


class mainBody(QObject):
    themeChangeSignal = Signal(str)
    statusUpdateSignal = Signal(str)

    def __init__(self, parent=None, themeEngine: theme_engine = None, projectEngine: project_engine = None,
                 settingsEngine: settings_engine = None, signalEngine: signals_engine = None):
        super().__init__(parent)
        self.parent = parent
        self.themeEngine: theme_engine = themeEngine
        self.projectEngine: project_engine = projectEngine
        self.settingsEngine: settings_engine = settingsEngine
        self.signalEngine: signals_engine = signalEngine

        self.bodyLayout: QHBoxLayout = QHBoxLayout(self.parent.body)
        self.bodyLayout.setContentsMargins(0, 0, 15, 0)
        self.bodyLayout.setSpacing(0)

        self.sideBar: QFrame = QFrame()
        self.homeButton: QPushButton = QPushButton("Home")
        self.seminAutoButton: QPushButton = QPushButton("semi")
        self.settingsButton: QPushButton = QPushButton("settings")
        self.sideBarLayout: QGridLayout = QGridLayout()
        self.sideBarLayout.addWidget(self.homeButton, 0, 0)
        self.sideBarLayout.addWidget(self.seminAutoButton, 1, 0)
        self.sideBarLayout.addWidget(self.settingsButton, 2, 0, Qt.AlignmentFlag.AlignBottom)
        self.sideBar.setLayout(self.sideBarLayout)

        self.mainPages: QStackedWidget = QStackedWidget()

        self.bodyLayout.addWidget(self.sideBar)
        self.bodyLayout.addWidget(self.mainPages)

        self._linkPages()
        self._setupObjectNames()
        self._setupStyling()
        self._setupConnections()

    def _linkPages(self):
        self.projectPage = UI_projectsPage(themeEngine=self.themeEngine, projectEngine=self.projectEngine,
                                           settingsEngine=self.settingsEngine, signalEngine=self.signalEngine)
        self.semiAutoPage = UI_semiAutoPage(themeEngine=self.themeEngine, projectEngine=self.projectEngine,
                                            settingsEngine=self.settingsEngine, signalEngine=self.signalEngine)

        self.mainPages.addWidget(self.projectPage)
        self.mainPages.addWidget(self.semiAutoPage)
        self.mainPages.setCurrentWidget(self.semiAutoPage)

    def _setupConnections(self):
        self.homeButton.clicked.connect(lambda: self.mainPages.setCurrentWidget(self.projectPage))
        self.seminAutoButton.clicked.connect(lambda: self.mainPages.setCurrentWidget(self.semiAutoPage))

    def _setupObjectNames(self):
        self.mainPages.setObjectName("mainPages")

    def _setupStyling(self):
        self.sideBar.setStyleSheet(f"""
                                    background-color: {self.themeEngine.get("primary")};
                                    """)
        sideBarButtonStyles: str = f"""
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
        for btn in [self.homeButton, self.seminAutoButton, self.settingsButton]:
            btn.setStyleSheet(sideBarButtonStyles)
            btn.setFixedSize(70,27)

        self.mainPages.setStyleSheet(f"""
                                    border:1px solid {self.themeEngine.get("accent_primary")};
                                    border-radius:{self.themeEngine.getProperty("border_radius_md")}      
                                            """)
