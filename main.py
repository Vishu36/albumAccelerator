import sys

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from ui_Elements.projectsPageDesign import UI_projectsPage
from ui_Elements.semiAutoPageDesign import UI_semiAutoPage
from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine
from ui_provider.window import window
import ui_Elements

from ui_Elements.bodyDesign import mainBody
from ui_Elements.photosPageDesign import UI_photosPage

from ui_Elements.photosPageDesign import UI_photosPage
from ui_Elements.projectsPageDesign import UI_projectsPage
from ui_Elements.semiAutoPageDesign import UI_semiAutoPage

import xmlrpc.client


def perform_search(search_query):
    return xmlrpc.client.ServerProxy("http://127.0.0.1:9000/").search(F"{search_query}")

class AlbumAccelerator(QApplication, QObject):
    def __init__(self):
        super().__init__(sys.argv)
        self._setupEngines()
        self.root = window(themeEngine=self.themeEngine, settingsEngine=self.settingsEngine,
                           projectEngine=self.projectEngine, windowID="root")
        self.loadUIs()
        self.setupConnections()
        self.root.show()

    def loadUIs(self):
        self.mainBody = mainBody(parent=self.root, themeEngine=self.themeEngine,
                                 settingsEngine=self.settingsEngine,
                                 projectEngine=self.projectEngine)

    def _setupEngines(self):
        self.signalEngine = signals_engine(parent=self)
        self.themeEngine = theme_engine()
        self.settingsEngine = settings_engine()
        self.projectEngine = project_engine()
        self.settingsEngine.load_settings()

    def setupConnections(self):
        self.projectEngine.onProjectLoaded.connect(self.onProjectLoaded)

    def onProjectLoaded(self):
        self.mainBody.mainPages.setCurrentWidget(self.mainBody.semiAutoPage)


def main():
    app = AlbumAccelerator()
    app.exec()

if __name__ == '__main__':
    main()