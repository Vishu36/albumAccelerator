import os

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt, QAbstractListModel, QModelIndex, QThreadPool, QRunnable, Signal)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform, QShortcut)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QListWidget,
                               QListWidgetItem, QSizePolicy, QWidget, QListView)

from ui_Elements.folderElementDesign import UI_folderElement
from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine

import thumb_engine
from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import QSize, QRect, Qt
from PySide6.QtGui import QPainter, QColor, QFontMetrics


def getThumbnail(imagePath, size=(150, 150)):
    img_bytes = thumb_engine.getThumb(imagePath, size, True)
    pixmap = QPixmap()
    pixmap.loadFromData(img_bytes, "PNG")
    return pixmap


class PhotoItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumb_size = 150  # Changed back to standard initial size
        self.scaled_cache = {}

    def sizeHint(self, option, index):
        return QSize(self.thumb_size + 20, self.thumb_size + 40)

    def setThumbSize(self, size):
        if self.thumb_size != size:
            self.thumb_size = size
            self.scaled_cache.clear()

    def paint(self, painter: QPainter, option, index):
        painter.save()

        name = index.data(Qt.ItemDataRole.DisplayRole)
        pixmap = index.data(Qt.ItemDataRole.DecorationRole)

        # We NO LONGER use row for the cache

        if option.state & QStyle.State_Selected:
            painter.setBrush(option.palette.highlight())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(option.rect, 5, 5)
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        padding = 10
        text_height = 20

        img_rect = QRect(
            option.rect.x() + (option.rect.width() - self.thumb_size) // 2,
            option.rect.y() + padding,
            self.thumb_size,
            self.thumb_size
        )

        if pixmap and not pixmap.isNull():
            # --- THE FIX IS HERE ---
            # cacheKey() returns a unique ID for the specific image data
            cache_key = pixmap.cacheKey()

            if cache_key not in self.scaled_cache:
                self.scaled_cache[cache_key] = pixmap.scaled(
                    self.thumb_size, self.thumb_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            scaled_pixmap = self.scaled_cache[cache_key]
            # -----------------------

            x_offset = (self.thumb_size - scaled_pixmap.width()) // 2
            y_offset = (self.thumb_size - scaled_pixmap.height()) // 2

            painter.drawPixmap(img_rect.x() + x_offset, img_rect.y() + y_offset, scaled_pixmap)
        else:
            painter.setBrush(QColor("#404040"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(img_rect, 4, 4)

        text_rect = QRect(
            option.rect.x() + padding,
            img_rect.bottom() + 5,
            option.rect.width() - (padding * 2),
            text_height
        )

        metrics = QFontMetrics(painter.font())
        elided_text = metrics.elidedText(name, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided_text)

        painter.restore()


class ThumbnailWorkerSignals(QObject):
    result_ready = Signal(int, int, bytes)


class ThumbnailWorker(QRunnable):
    # CHANGED: Request the MAX zoom size so scaling down looks sharp
    def __init__(self, generation_id, row_index, image_path, size=(256, 256)):
        super().__init__()
        self.generation_id = generation_id
        self.row_index = row_index
        self.image_path = image_path
        self.size = size
        self.signals = ThumbnailWorkerSignals()

    def run(self):
        try:
            img_bytes = thumb_engine.getThumb(self.image_path, self.size, False)
            if img_bytes:
                self.signals.result_ready.emit(self.generation_id, self.row_index, img_bytes)
        except Exception as e:
            print(f"Error loading thumbnail for {self.image_path}: {e}")


class photosViewModel(QAbstractListModel):
    def __init__(self, images=None):
        super().__init__()
        self.images = images or []

        # NEW: Create a dedicated thread pool just for thumbnails
        self.thread_pool = QThreadPool()
        # Pro-tip: Leave at least one CPU core free for the main UI thread
        import multiprocessing
        max_threads = max(1, multiprocessing.cpu_count() - 1)
        self.thread_pool.setMaxThreadCount(max_threads)

        self.thumbnail_cache = {}
        self.current_generation = 0

        self.placeholder = QPixmap(150, 150)
        self.placeholder.fill(QColor("#e0e0e0"))

    def rowCount(self, parent=QModelIndex()):
        return len(self.images)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # Explicitly guarantee the item can be clicked and selected
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    # ---------------------------
    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        image = self.images[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return image.get("name", "")

        if role == Qt.ItemDataRole.DecorationRole:
            if image.get("thumb"):
                return QPixmap.fromImage(QImage.fromData(image["thumb"]))
            if row in self.thumbnail_cache:
                return self.thumbnail_cache[row]
            return None  # Delegate will draw placeholder if None

        if role == Qt.ItemDataRole.UserRole:
            return image

        return None

    def updateImages(self, new_images):
        self.beginResetModel()
        self.images = new_images
        self.thumbnail_cache.clear()
        self.current_generation += 1

        # CRITICAL FIX: Delete all pending workers from the previous folder
        # This stops the app from crashing or lagging when switching folders rapidly
        self.thread_pool.clear()

        self.endResetModel()

        for row, image in enumerate(self.images):
            if not image.get("thumb"):
                worker = ThumbnailWorker(self.current_generation, row, image.get("path"))
                worker.signals.result_ready.connect(self._on_thumbnail_loaded)
                self.thread_pool.start(worker)

    def _on_thumbnail_loaded(self, generation_id, row, img_bytes):
        if generation_id != self.current_generation:
            return

        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes, "PNG")
        self.thumbnail_cache[row] = pixmap

        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, [Qt.ItemDataRole.DecorationRole])

class UI_photosPage(QWidget):
    # Removed redundant QObject
    def __init__(self, themeEngine, projectEngine, settingsEngine, signalEngine):
        super().__init__()
        self.themeEngine = themeEngine
        self.projectEngine = projectEngine
        self.settingsEngine = settingsEngine
        self.signalEngine = signalEngine

        # Zoom Constraints and State
        self.current_thumb_size = 150
        self.min_thumb_size = 64
        self.max_thumb_size = 256
        self.zoom_step = 20

        pgLayout = QGridLayout(self)
        pgLayout.setSpacing(0)
        pgLayout.setHorizontalSpacing(5)
        pgLayout.setContentsMargins(0, 0, 0, 0)

        self.folderViewElement = UI_folderElement(
            self, themeEngine=self.themeEngine,
            settingsEngine=self.settingsEngine,
            projectEngine=self.projectEngine, signalEngine=self.signalEngine
        )

        self.folderViewElement.setMinimumSize(QSize(200, 0))
        self.folderViewElement.setMaximumSize(QSize(200, 16777215))

        self.imageView = QListView(self)

        pgLayout.addWidget(self.folderViewElement, 0, 0, 1, 1)
        pgLayout.addWidget(self.imageView, 0, 1, 1, 1)

        self._setStyling()
        self.__setupImageViewModel()
        self.__setupShortcuts()

    def _setStyling(self):
        self.imageView.setStyleSheet(f"""
            background-color:{self.themeEngine.get("primary")};
            border:1px solid {self.themeEngine.get("accent_primary")};
        """)

    def __setupImageViewModel(self):
        self.photosViewModel = photosViewModel()
        self.imageView.setModel(self.photosViewModel)

        # --- CHANGED: Connect to our new coordinator method below ---
        self.folderViewElement.onFolderClicked.connect(self._handleNewFolder)

        # Apply Custom Delegate
        self.photoDelegate = PhotoItemDelegate(self.imageView)
        self.imageView.setItemDelegate(self.photoDelegate)

        # ListView View Setup
        self.imageView.setViewMode(QListView.ViewMode.IconMode)
        self.imageView.setResizeMode(QListView.ResizeMode.Adjust)
        self.imageView.setUniformItemSizes(True)
        self.imageView.setWordWrap(True)

        # Apply initial sizing
        self._updateGridSizes()

    def _handleNewFolder(self, images):
        # 1. Brutally wipe the delegate's image cache so no old images survive
        self.photoDelegate.scaled_cache.clear()

        # 2. Tell the model to load the new images
        self.photosViewModel.updateImages(images)

    def __setupShortcuts(self):
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._zoomIn)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._zoomIn)

        # Zoom Out
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._zoomOut)

    def _zoomIn(self):
        if self.current_thumb_size < self.max_thumb_size:
            self.current_thumb_size = min(self.current_thumb_size + self.zoom_step, self.max_thumb_size)
            self._updateGridSizes()

    def _zoomOut(self):
        if self.current_thumb_size > self.min_thumb_size:
            self.current_thumb_size = max(self.current_thumb_size - self.zoom_step, self.min_thumb_size)
            self._updateGridSizes()

    def _updateGridSizes(self):
        self.photoDelegate.setThumbSize(self.current_thumb_size)

        grid_width = self.current_thumb_size + 20
        grid_height = self.current_thumb_size + 40
        self.imageView.setGridSize(QSize(grid_width, grid_height))

        # --- ADD THIS LINE ---
        # This forces the QListView to throw away its cached sizes
        # and ask the delegate for the new sizeHint() immediately.
        self.imageView.doItemsLayout()
