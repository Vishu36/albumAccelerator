import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)

from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.theme_engine import theme_engine


class SideGrip(QWidget):
    def __init__(self, parent, edge):
        super().__init__(parent)
        self.edge = edge
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: transparent;")

        # --- Handle Combinations for Corners ---
        if edge == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or \
                edge == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)

        elif edge == (Qt.Edge.TopEdge | Qt.Edge.RightEdge) or \
                edge == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)

        elif edge in (Qt.Edge.TopEdge, Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeVerCursor)

        elif edge in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeHorCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # startSystemResize relies on the native window handle
            self.window().windowHandle().startSystemResize(self.edge)


class window(QWidget):
    def __init__(self
                 , themeEngine: theme_engine
                 , settingsEngine: settings_engine
                 , projectEngine: project_engine, windowID: str = None):

        super().__init__()
        self.themeEngine = themeEngine
        self.settingsEngine = settingsEngine
        self.projectsEngine = projectEngine
        self.winID = windowID

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        try:
            self.resize(self.settingsEngine.get("window_size_" + self.winID)[0],
                        self.settingsEngine.get("window_size_" + self.winID)[1])

            self.move(self.settingsEngine.get("window_pos_" + self.winID)[0],
                      self.settingsEngine.get("window_pos_" + self.winID)[1])
        except:
            self.settingsEngine.set("window_pos_" + self.winID, [])
            self.settingsEngine.set("window_pos_" + self.winID, [])

        self.titleBar = QFrame(self)
        self.body = QFrame(self)
        self.statusBar = QFrame(self)

        self.titleText = QLabel("My Frameless Window", self.titleBar)
        self.minBtn = QPushButton("🗕", self.titleBar)
        self.maxBtn = QPushButton("🗖", self.titleBar)
        self.closeBtn = QPushButton("✕", self.titleBar)

        # 3. Layouts
        self._winLayout = QVBoxLayout(self)
        self._winLayout.setContentsMargins(0, 0, 0, 0)
        self._winLayout.setSpacing(0)

        self._titleBarLayout = QHBoxLayout(self.titleBar)
        self._titleBarLayout.setContentsMargins(10, 0, 10, 0)
        self._titleBarLayout.addWidget(self.titleText)
        self._titleBarLayout.addStretch()
        self._titleBarLayout.addWidget(self.minBtn)
        self._titleBarLayout.addWidget(self.maxBtn)
        self._titleBarLayout.addWidget(self.closeBtn)

        self._winLayout.addWidget(self.titleBar)
        self._winLayout.addWidget(self.body, 1)  # Stretch factor 1 makes body expand
        self._winLayout.addWidget(self.statusBar)

        # 4. Connect Buttons & TitleBar Dragging
        self.minBtn.clicked.connect(self.showMinimized)
        self.maxBtn.clicked.connect(self._toggle_maximize)
        self.closeBtn.clicked.connect(self.close)

        # Make the title bar draggable using system move
        self.titleBar.mousePressEvent = self._move_window

        # 5. Initialize Side Grips
        self._grip_size = 5
        self.grips = {
            "top": SideGrip(self, Qt.Edge.TopEdge),
            "bottom": SideGrip(self, Qt.Edge.BottomEdge),
            "left": SideGrip(self, Qt.Edge.LeftEdge),
            "right": SideGrip(self, Qt.Edge.RightEdge),
            "top_left": SideGrip(self, Qt.Edge.TopEdge | Qt.Edge.LeftEdge),
            "top_right": SideGrip(self, Qt.Edge.TopEdge | Qt.Edge.RightEdge),
            "bottom_left": SideGrip(self, Qt.Edge.BottomEdge | Qt.Edge.LeftEdge),
            "bottom_right": SideGrip(self, Qt.Edge.BottomEdge | Qt.Edge.RightEdge),
        }

        # 6. Apply Styles
        self._setupStylings()
        self.windowTitleChanged.connect(lambda: self.titleText.setText(self.windowTitle()))

    def _move_window(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()

    def _toggle_maximize(self):
        """Toggles between maximized and normal window states."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def resizeEvent(self, event):
        """Update the geometry of the grips whenever the window is resized."""
        super().resizeEvent(event)

        w = self.width()
        h = self.height()
        s = self._grip_size

        # Position edges
        self.grips["top"].setGeometry(s, 0, w - 2 * s, s)
        self.grips["bottom"].setGeometry(s, h - s, w - 2 * s, s)
        self.grips["left"].setGeometry(0, s, s, h - 2 * s)
        self.grips["right"].setGeometry(w - s, s, s, h - 2 * s)

        # Position corners
        self.grips["top_left"].setGeometry(0, 0, s, s)
        self.grips["top_right"].setGeometry(w - s, 0, s, s)
        self.grips["bottom_left"].setGeometry(0, h - s, s, s)
        self.grips["bottom_right"].setGeometry(w - s, h - s, s, s)

        # Raise grips to the top of the widget stack so they aren't blocked by the body/titlebar
        for grip in self.grips.values():
            grip.raise_()

        self.settingsEngine.set("window_size_" + self.winID, [self.width(), self.height()])

    def _setupStylings(self):
        self.titleBar.setFixedHeight(self.themeEngine.getProperty("title_bar_height"))
        self.statusBar.setFixedHeight(self.themeEngine.getProperty("status_bar_height"))

        self.titleBar.setStyleSheet(f"""
            background-color: {self.themeEngine.get("primary")};
            border-top-right-radius:{self.themeEngine.getProperty("border_radius_lg")};
            border-top-left-radius:{self.themeEngine.getProperty("border_radius_lg")};
        """)
        self.statusBar.setStyleSheet(f"""
                    background-color: {self.themeEngine.get("primary")};
                    border-bottom-right-radius:{self.themeEngine.getProperty("border_radius_lg")};
                    border-bottom-left-radius:{self.themeEngine.getProperty("border_radius_lg")};
                """)

        self.body.setStyleSheet(f"""
            background-color: {self.themeEngine.get("primary")};
            
            """)

        self.titleText.setStyleSheet(f"""
                font: {self.themeEngine.getFont("title")};
                color: {self.themeEngine.get("text")};
        """)
        print(self.themeEngine.getFont("title"))

        btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: white;
                border: none;
                font: {self.themeEngine.get("title_bar_font")};
                font-size: 14px;                
                padding: 5px 8px;
                border-radius: {self.themeEngine.getProperty("border_radius_sm")}px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 30);
            }}
        """
        self.minBtn.setStyleSheet(btn_style)
        self.maxBtn.setStyleSheet(btn_style)

        self.closeBtn.setStyleSheet(btn_style + """
            QPushButton:hover {
                background-color: #e81123;
            }
        """)

    def moveEvent(self, event, /):
        self.settingsEngine.set("window_pos_" + self.winID, [self.x(), self.y()])


if __name__ == '__main__':
    TH = theme_engine()
    ST = settings_engine()
    ST.load_settings()
    PM = project_engine()
    app = QApplication(sys.argv, )
    w = window(themeEngine=TH, settingsEngine=ST, projectEngine=PM, windowID="app_root")
    w.show()
    sys.exit(app.exec())
