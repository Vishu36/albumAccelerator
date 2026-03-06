import os

from PySide6.QtCore import (QObject, QSize, QRect, Qt, QAbstractListModel, QModelIndex,
                            QThreadPool, QRunnable, Signal, QMimeData, QUrl)
from PySide6.QtGui import (QColor, QPixmap, QImage, QPainter, QFontMetrics, QKeySequence, QShortcut)
from PySide6.QtWidgets import (QWidget, QGridLayout, QListView, QStyledItemDelegate, QStyle, QMenu)

from ui_Elements.folderElementDesign import UI_folderElement
from ui_provider.project_engine import project_engine
from ui_provider.settings_engine import settings_engine
from ui_provider.signals_engine import signals_engine
from ui_provider.theme_engine import theme_engine

import thumb_engine


class PhotoItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumb_size = 150
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
        image_data = index.data(Qt.ItemDataRole.UserRole)

        is_used = image_data.get("used", False) if image_data else False
        is_highlight = image_data.get("highlight", False) if image_data else False

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
            cache_key = pixmap.cacheKey()
            if cache_key not in self.scaled_cache:
                self.scaled_cache[cache_key] = pixmap.scaled(
                    self.thumb_size, self.thumb_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            scaled_pixmap = self.scaled_cache[cache_key]
            x_offset = (self.thumb_size - scaled_pixmap.width()) // 2
            y_offset = (self.thumb_size - scaled_pixmap.height()) // 2

            # Draw the image
            painter.drawPixmap(img_rect.x() + x_offset, img_rect.y() + y_offset, scaled_pixmap)

            # If used, draw a semi-transparent dark overlay to dim the image
            if is_used:
                overlay_rect = QRect(img_rect.x() + x_offset, img_rect.y() + y_offset, scaled_pixmap.width(),
                                     scaled_pixmap.height())
                painter.fillRect(overlay_rect, QColor(0, 0, 0, 100))  # 100 out of 255 opacity
        else:
            painter.setBrush(QColor("#404040"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(img_rect, 4, 4)

        # --- DRAW STATUS BADGES ---
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        badge_size = 24
        margin = 6
        icon_font = painter.font()
        icon_font.setPixelSize(14)
        icon_font.setBold(True)
        painter.setFont(icon_font)

        if is_used:
            used_rect = QRect(img_rect.left() + margin, img_rect.top() + margin, badge_size, badge_size)
            painter.setBrush(QColor("#4CAF50"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(used_rect)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(used_rect, Qt.AlignmentFlag.AlignCenter, "✓")

        if is_highlight:
            star_rect = QRect(img_rect.right() - badge_size - margin, img_rect.top() + margin, badge_size, badge_size)
            painter.setBrush(QColor("#FFC107"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(star_rect)
            painter.setPen(QColor("#000000"))
            painter.drawText(star_rect, Qt.AlignmentFlag.AlignCenter, "★")

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        # --------------------------

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
            pass


class photosViewModel(QAbstractListModel):
    orientationRole = Qt.ItemDataRole.UserRole + 1
    pathRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, images=None):
        super().__init__()
        self.images = images or []
        self.thread_pool = QThreadPool()
        import multiprocessing
        self.thread_pool.setMaxThreadCount(max(1, multiprocessing.cpu_count() - 1))
        self.thumbnail_cache = {}
        self.current_generation = 0
        self.placeholder = QPixmap(150, 150)
        self.placeholder.fill(QColor("#e0e0e0"))

    def rowCount(self, parent=QModelIndex()):
        return len(self.images)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled

    def mimeTypes(self):
        # Tell Qt we are dragging file paths (URIs)
        return ["text/uri-list"]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        urls = []

        # Loop through all selected items being dragged
        for index in indexes:
            if index.isValid():
                image_data = self.images[index.row()]
                path = image_data.get("path")
                if path:
                    # Convert the raw text path into a proper OS file URL
                    urls.append(QUrl.fromLocalFile(path))

        mime_data.setUrls(urls)
        return mime_data

    def data(self, index, role):
        if not index.isValid(): return None
        row = index.row()
        image = self.images[row]

        if role == Qt.ItemDataRole.DisplayRole: return image.get("name", "")
        if role == Qt.ItemDataRole.DecorationRole:
            if image.get("thumb"): return QPixmap.fromImage(QImage.fromData(image["thumb"]))
            if row in self.thumbnail_cache: return self.thumbnail_cache[row]
            return None
        if role == self.orientationRole:
            return image.get("orientation")
        if role == self.pathRole:
            return image.get("path")

        if role == Qt.ItemDataRole.UserRole: return image
        return None

    def updateImages(self, new_images):
        self.beginResetModel()
        self.images = new_images
        self.thumbnail_cache.clear()
        self.current_generation += 1
        self.thread_pool.clear()
        self.endResetModel()

        for row, image in enumerate(self.images):
            if not image.get("thumb"):
                worker = ThumbnailWorker(self.current_generation, row, image.get("path"))
                worker.signals.result_ready.connect(self._on_thumbnail_loaded)
                self.thread_pool.start(worker)

    def _on_thumbnail_loaded(self, generation_id, row, img_bytes):
        if generation_id != self.current_generation: return
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes, "PNG")
        self.thumbnail_cache[row] = pixmap
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, [Qt.ItemDataRole.DecorationRole])

    def updateItemData(self, rows_to_update: list, key: str, value):
        for row in rows_to_update:
            if 0 <= row < len(self.images):
                self.images[row][key] = value
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.UserRole])

    def removeItems(self, rows_to_remove: list):
        for row in sorted(rows_to_remove, reverse=True):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.images[row]
            if row in self.thumbnail_cache:
                del self.thumbnail_cache[row]
            self.endRemoveRows()

    def refreshThumbnails(self, rows_to_refresh: list):
        for row in rows_to_refresh:
            image = self.images[row]
            if row in self.thumbnail_cache:
                del self.thumbnail_cache[row]
            worker = ThumbnailWorker(self.current_generation, row, image.get("path"))
            worker.signals.result_ready.connect(self._on_thumbnail_loaded)
            self.thread_pool.start(worker)


class UI_photosPage(QWidget):
    imagesSelected = Signal(str, list)

    def __init__(self, themeEngine, projectEngine, settingsEngine, signalEngine):
        super().__init__()
        self.themeEngine = themeEngine
        self.projectEngine = projectEngine
        self.settingsEngine = settingsEngine
        self.signalEngine = signalEngine

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
        self.folderViewElement.onFolderClicked.connect(self._handleNewFolder)

        self.photoDelegate = PhotoItemDelegate(self.imageView)
        self.imageView.setItemDelegate(self.photoDelegate)

        self.imageView.setViewMode(QListView.ViewMode.IconMode)
        self.imageView.setResizeMode(QListView.ResizeMode.Adjust)
        self.imageView.setUniformItemSizes(True)
        self.imageView.setWordWrap(True)

        # Enable Context Menu
        self.imageView.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.imageView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.imageView.customContextMenuRequested.connect(self._showContextMenu)

        self.imageView.setDragEnabled(True)
        self.imageView.setDragDropMode(QListView.DragDropMode.DragOnly)
        self.imageView.selectionModel().selectionChanged.connect(self._onSelectionChanged)
        self._updateGridSizes()

    def _onSelectionChanged(self, selected, deselected):
        selected_indexes = self.imageView.selectionModel().selectedIndexes()
        f = len(selected_indexes)
        v = 0
        h = 0
        selectetImages = []
        for i in selected_indexes:
            ori = i.data(self.photosViewModel.orientationRole)
            if ori.lower() == "v":
                v = v + 1
            if ori.lower() == "h":
                h = h + 1
            selectetImages.append(i.data(self.photosViewModel.pathRole))
        compatiblePsd = f"""{f}F{h}H{v}V"""
        self.imagesSelected.emit(compatiblePsd, selectetImages)
        
    def _handleNewFolder(self, images):
        self.photoDelegate.scaled_cache.clear()
        self.photosViewModel.updateImages(images)

    def __setupShortcuts(self):
        shortcut_zoom_in_1 = QShortcut(QKeySequence("Ctrl++"), self.imageView)
        # 2. Restrict the context so it ONLY fires when the list has focus
        shortcut_zoom_in_1.setContext(Qt.WidgetShortcut)
        shortcut_zoom_in_1.activated.connect(self._zoomIn)

        shortcut_zoom_in_2 = QShortcut(QKeySequence("Ctrl+="), self.imageView)
        shortcut_zoom_in_2.setContext(Qt.WidgetShortcut)
        shortcut_zoom_in_2.activated.connect(self._zoomIn)

        shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self.imageView)
        shortcut_zoom_out.setContext(Qt.WidgetShortcut)
        shortcut_zoom_out.activated.connect(self._zoomOut)

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
        self.imageView.doItemsLayout()

    def _showContextMenu(self, pos):
        selected_indexes = self.imageView.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.themeEngine.get("secondary")};
                color: {self.themeEngine.get("text")};
                border: 1px solid {self.themeEngine.get("accent_primary")};
            }}
            QMenu::item:selected {{ background-color: {self.themeEngine.get("accent_hover")}; }}
        """)

        action_mark_used = menu.addAction("Mark as Used")
        action_mark_unused = menu.addAction("Mark as Unused")
        action_toggle_highlight = menu.addAction("Toggle Highlight")
        menu.addSeparator()
        action_refresh_thumbs = menu.addAction("Refresh Thumbnail(s)")
        menu.addSeparator()
        action_rotate_cw = menu.addAction("Rotate Clockwise ↻")
        action_rotate_ccw = menu.addAction("Rotate Anti-Clockwise ↺")
        menu.addSeparator()
        action_remove = menu.addAction("Remove from Project")

        chosen_action = menu.exec(self.imageView.viewport().mapToGlobal(pos))

        rows = [idx.row() for idx in selected_indexes]
        paths = [idx.data(Qt.ItemDataRole.UserRole).get("path") for idx in selected_indexes]

        if chosen_action == action_mark_used:
            self.projectEngine.setImagesUsed(paths, 1)
            self.photosViewModel.updateItemData(rows, "used", True)

        elif chosen_action == action_mark_unused:
            self.projectEngine.setImagesUsed(paths, 0)
            self.photosViewModel.updateItemData(rows, "used", False)

        elif chosen_action == action_toggle_highlight:
            self.projectEngine.toggleImagesHighlight(paths)
            for r in rows:
                current_state = self.photosViewModel.images[r].get("highlight", False)
                self.photosViewModel.updateItemData([r], "highlight", not current_state)

        elif chosen_action == action_remove:
            self.projectEngine.removeImages(paths)
            self.photosViewModel.removeItems(rows)

        elif chosen_action == action_refresh_thumbs:
            self.photosViewModel.refreshThumbnails(rows)

        elif chosen_action == action_rotate_cw:
            self.projectEngine.rotateRealImages(paths, -90)
            self.photosViewModel.refreshThumbnails(rows)

        elif chosen_action == action_rotate_ccw:
            self.projectEngine.rotateRealImages(paths, 90)
            self.photosViewModel.refreshThumbnails(rows)
