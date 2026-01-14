import os
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QFileSystemModel

from .config_manager import ConfigManager
from .res import rc_arkadisti  # noqa: F401
from .ui.ui_screenshot_window import Ui_ScreenshotWindow


class ScreenshotWindow(QDialog):
    def __init__(self, game):
        super().__init__()

        self.config = ConfigManager()

        self.current = None

        snap_dir = (self.config.get_snap_dir() / game).resolve()

        self.ui = Ui_ScreenshotWindow()
        self.ui.setupUi(self)

        self.setFixedSize(self.size())
        self.setWindowFlags(
            Qt.WindowMinimizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        icon = QIcon(":/icons/arkadisti.svg")
        self.setWindowIcon(icon)

        self.model = QFileSystemModel()
        self.model.setRootPath(str(snap_dir))
        self.model.setNameFilters(
            ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"]
        )
        self.model.setNameFilterDisables(False)

        if snap_dir.exists():
            self.ui.imageView.setModel(self.model)
            self.ui.imageView.setRootIndex(self.model.index(str(snap_dir)))
            self.ui.imageView.setUniformItemSizes(True)
            self.ui.imageView.clicked.connect(self.update_preview)
            self.ui.imageView.selectionModel().currentChanged.connect(
                self.update_preview
            )

    def accept(self):
        if self.current:
            self.result_data = Path(self.current)
        else:
            self.result_data = self.current
        super().accept()

    def update_preview(self, current: QModelIndex, *_):
        file_path = self.model.filePath(current)
        self.current = file_path
        if os.path.isfile(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.ui.imageLabel.setPixmap(pixmap)
            else:
                self.ui.imageLabel.setText("Nemohu načíst obrázek")
        else:
            self.ui.imageLabel.setText("Vyber obrázek")
