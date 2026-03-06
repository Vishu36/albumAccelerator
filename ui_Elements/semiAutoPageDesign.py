from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QGridLayout,
                               QHBoxLayout, QPushButton, QSizePolicy, QStackedWidget,
                               QWidget)

from ui_Elements.photosPageDesign import UI_photosPage
from ui_Elements.toolsPageDesign import toolsPageDesign
from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine


class UI_semiAutoPage(QWidget, QObject):
    def __init__(self, themeEngine, projectEngine,
                 settingsEngine, signalEngine):
        super().__init__()
        self.themeEngine: theme_engine = themeEngine
        self.projectEngine: project_engine = projectEngine
        self.settingsEngine: settings_engine = settingsEngine
        self.signalEngine: signals_engine = signalEngine

        self.navBar = QFrame(self)
        self.navBar.setFixedHeight(23)
        self.navBar.setFrameShape(QFrame.Shape.StyledPanel)
        self.navBar.setFrameShadow(QFrame.Shadow.Raised)
        self.navBarLayout = QHBoxLayout(self.navBar)
        self.navBarLayout.setSpacing(5)
        self.navBarLayout.setContentsMargins(0, 0, 0, 0)

        self.photosButton = QPushButton(self.navBar)
        self.templatesButton = QPushButton(self.navBar)
        self.backgroundButton = QPushButton(self.navBar)
        self.clipArtButton = QPushButton(self.navBar)
        self.toolsButton = QPushButton(self.navBar)

        self.toolsButton.setMaximumSize(QSize(60, 16777215))

        self.semiPages = QStackedWidget(self)

        self.toolsPanel = toolsPageDesign(self, themeEngine, projectEngine,
                 settingsEngine, signalEngine)


        self.photosButton.setText("Photos")
        self.templatesButton.setText(u"Templates")
        self.backgroundButton.setText(u"Backgrounds")
        self.clipArtButton.setText(u"Clip-Arts")
        self.toolsButton.setText(u"Tools")

        self.setupLayout()

        self._pageLinking()

        self.styling()

    def _pageLinking(self):
        self.photosPage = UI_photosPage(themeEngine=self.themeEngine, settingsEngine=self.settingsEngine,
                                        projectEngine=self.projectEngine, signalEngine=self.signalEngine)

        self.semiPages.addWidget(self.photosPage)
        self.semiPages.setCurrentWidget(self.photosPage)

    def setupLayout(self):
        pgLayout = QGridLayout(self)
        pgLayout.setSpacing(5)
        pgLayout.setHorizontalSpacing(5)
        pgLayout.setContentsMargins(5, 5, 5, 5)
        pgLayout.addWidget(self.navBar, 0, 0, 1, 2)
        pgLayout.addWidget(self.semiPages, 1, 0, 1, 1)
        pgLayout.addWidget(self.toolsPanel, 1, 1, 1, 1)

        self.semiAutoNavBarBtnGroup = QButtonGroup(self)
        self.semiAutoNavBarBtnGroup.addButton(self.photosButton)
        self.semiAutoNavBarBtnGroup.addButton(self.backgroundButton)
        self.semiAutoNavBarBtnGroup.addButton(self.clipArtButton)
        self.semiAutoNavBarBtnGroup.addButton(self.templatesButton)

        self.navBarLayout.addWidget(self.photosButton)
        self.navBarLayout.addWidget(self.templatesButton)
        self.navBarLayout.addWidget(self.backgroundButton)
        self.navBarLayout.addWidget(self.clipArtButton)
        self.navBarLayout.addWidget(self.toolsButton, 0, Qt.AlignmentFlag.AlignRight)

    def styling(self):

        self.navBar.setStyleSheet(f"""
                                   border-bottom-left-radius: 0px; 
                                   border-bottom-rigth-radius: 0px; 
                                   border:0;
                                    """)
        self.semiPages.setStyleSheet(f"""
                                    background-color:{self.themeEngine.get("primary")};
                                    border:0;
                                    border-radius:{self.themeEngine.getProperty("border_radius_sm")}
                                    """)
        self.toolsPanel.setStyleSheet(f"""
                                    sbackground-color:{self.themeEngine.get("secondary")};
                                    smin-width:250px;max-width:300px;
                                    sborder-radius:{self.themeEngine.getProperty("border_radius_sm")}
                                    """)

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
        for btn in [self.photosButton, self.templatesButton, self.backgroundButton, self.clipArtButton,
                    self.toolsButton]:
            btn.setStyleSheet(btnStyle)
            btn.setFixedHeight(23)
            btn.setFixedWidth(100)
