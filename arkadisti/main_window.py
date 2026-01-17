import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import requests
from PySide6.QtCore import QModelIndex, Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from .config_manager import ConfigManager
from .games_model import GamesModel
from .res import rc_arkadisti  # noqa: F401
from .results_model import ResultsModel
from .scraper import Scraper
from .screenshot_window import ScreenshotWindow
from .settings_dialog import SettingsDialog
from .ui.ui_main_window import Ui_MainWindow

STORE_FILE = "store.h5"


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_game = None
        self.selected_input = None

        self.config = ConfigManager()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setFixedSize(self.size())
        self.setWindowFlags(
            Qt.WindowMinimizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.statusBar().setSizeGripEnabled(False)

        # icon = QIcon("res/arkadisti.svg")
        icon = QIcon(":/icons/arkadisti.svg")
        self.setWindowIcon(icon)

        self.model = GamesModel()
        self.ui.gamesView.setModel(self.model)
        self.ui.gamesView.selectionModel().currentChanged.connect(
            self.on_selection_changed
        )

        self.results_model = ResultsModel()
        self.ui.resultsTable.setModel(self.results_model)
        self.ui.resultsTable.verticalHeader().setVisible(False)

        self.ui.playButton.clicked.connect(self.play_button_pressed)
        self.ui.replayButton.clicked.connect(self.replay_button_pressed)
        self.ui.settingsButton.clicked.connect(self.settings_button_pressed)
        self.ui.downloadButton.clicked.connect(self.download_button_pressed)

        shortcut_f1 = QShortcut(QKeySequence("F1"), self)
        shortcut_f1.activated.connect(self.play_button_pressed)

        shortcut_enter = QShortcut(QKeySequence("Enter"), self)
        shortcut_enter.activated.connect(self.play_button_pressed)

        shortcut_return = QShortcut(QKeySequence("Return"), self)
        shortcut_return.activated.connect(self.play_button_pressed)

        self.ui.gamesView.doubleClicked.connect(self.play_button_pressed)

        shortcut_f2 = QShortcut(QKeySequence("F2"), self)
        shortcut_f2.activated.connect(self.replay_button_pressed)

        shortcut_f3 = QShortcut(QKeySequence("F3"), self)
        shortcut_f3.activated.connect(self.download_button_pressed)

        QTimer.singleShot(1, self.data_check)

    def data_check(self):
        games_count = self.model.rowCount(QModelIndex)
        if games_count == 0:
            self.download_button_pressed()
            first_index = self.model.index(0, 0)
            self.ui.gamesView.setCurrentIndex(first_index)

    def play_button_pressed(self):
        if self.selected_game:
            game = self.selected_game
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            mame_binary_path = self.config.get_mame_binary().resolve()
            inp_file = Path(game + "_" + current_time + ".inp")

            if not mame_binary_path.exists():
                QMessageBox.warning(
                    self, "Warning", "MAME nenalezeno: %s" % (mame_binary_path)
                )
                return

            command = [
                mame_binary_path,
                game,
                "-record",
                str(inp_file),
                "-input_directory",
                self.config.get_inp_dir(),
                "-snapshot_directory",
                self.config.get_snap_dir(),
            ]
            self.log("Spouštím: " + " ".join(str(x) for x in command))
            result = subprocess.run(
                command, cwd=".", capture_output=True, text=True
            )
            if result.returncode != 0:
                QMessageBox.warning(self, "Error", result.stderr)
            else:
                screenshot_dlg = ScreenshotWindow(game)
                if screenshot_dlg.exec():
                    self.zip_inp(inp_file)
                    screenshot_file = screenshot_dlg.result_data
                    if not screenshot_file:
                        QMessageBox.warning(
                            self,
                            "Poznámka",
                            "Nebyl vybrán žádný screenshot, "
                            "zkopírován pouze inp soubor."
                        )
                    else:
                        shutil.copy(
                            screenshot_dlg.result_data,
                            Path(self.config.get_output_dir())
                            / Path(inp_file.stem).with_suffix(
                                screenshot_file.suffix
                            ),
                        )
                        self.log("Vybrany screenshot %s"
                                 % (str(screenshot_file)))
        else:
            QMessageBox.warning(self, "Warning", "Není vybrána žádná hra!")

    def zip_inp(self, inp_file):
        zip_file = (
            self.config.get_output_dir()
            / Path(inp_file.stem).with_suffix(".zip")
        ).resolve()

        with zipfile.ZipFile(zip_file, "w") as zip_file_handle:
            zip_file_handle.write(
                self.config.get_inp_dir() / inp_file, inp_file
            )

    def settings_button_pressed(self):
        dlg = SettingsDialog()
        dlg.exec()

    def download_button_pressed(self):
        self.log("Stahuji data...(může trva pár sekund)")
        Scraper.download()
        self.log("Data stažena")
        self.model.reload()
        self.results_model.reload(self.selected_game)

    def replay_button_pressed(self):
        if not self.selected_input:
            QMessageBox.warning(self, "Warning", "Není vybrán žádný záznam!")
            return
        url = self.selected_input

        filename = Path(str(uuid4()) + ".inp")
        filename_store = self.config.get_inp_dir() / filename

        # Download ZIP into memory
        self.log("Stahuji %s" % (url))
        response = requests.get(url)
        zip_data = BytesIO(response.content)

        # Open ZIP from memory
        with zipfile.ZipFile(zip_data) as z:
            original_name = z.namelist()[0]
            data = z.read(original_name)

            with open(filename_store, "wb") as f:
                f.write(data)
            # z.extractall("output_folder")   # <-- extracted files go here
        command = [
            self.config.get_mame_binary().resolve(),
            self.selected_game,
            "-playback",
            filename,
            "-input_directory",
            self.config.get_inp_dir(),
        ]
        self.log("Spouštím: " + " ".join(str(x) for x in command))
        _ = subprocess.run(
            command, cwd=".", capture_output=True, text=True
        )

        filename_store.unlink(missing_ok=True)

    def on_selection_changed(self, current: QModelIndex, *_):
        index = self.ui.gamesView.currentIndex()
        game = index.data()

        # self.results_model = ResultsModel(game)
        # self.ui.resultsTable.setModel(self.results_model)
        self.results_model.reload(game)
        self.ui.resultsTable.hideColumn(4)
        self.ui.resultsTable.hideColumn(5)
        self.ui.resultsTable.hideColumn(6)

        self.ui.resultsTable.selectionModel().currentChanged.connect(
            self.on_selection_changed_table
        )

        self.selected_game = game
        self.selected_avatar = None
        self.selected_input = None
        self.selected_screenshot = None

    def on_selection_changed_table(self, current: QModelIndex, *_):
        index = self.ui.resultsTable.currentIndex()
        row = index.row()
        self.selected_input = self.results_model.index(row, 5).data()
        self.selected_screenshot = self.results_model.index(row, 6).data()
        self.selected_avatar = self.results_model.index(row, 4).data()

    def log(self, msg: str):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_out = str("[%s] %s" % (str(current_time), msg))
        self.ui.logView.append(msg_out)
        QApplication.processEvents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
