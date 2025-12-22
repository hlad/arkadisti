import configparser

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

LABELS = {
    "mame_binary": "mame_binary",
    "roms_dir": "roms_dir",
    "inp_dir": "inp_dir",
    "snap_dir": "snap_dir",
    "output_dir": "output_dir",
}

CONFIG_FILE = "settings.ini"


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Nastavení")
        self.setMinimumWidth(300)

        self.ini_path = CONFIG_FILE
        self.config = configparser.ConfigParser()
        self.config.read(self.ini_path)

        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.fields = {}

        for section in self.config.sections():
            for key, value in self.config[section].items():
                edit = QLineEdit(value)
                self.form_layout.addRow(f"{LABELS[key]}:", edit)
#                self.form_layout.addRow(f"{key}:", edit)
                self.fields[(section, key)] = edit

        layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Uložit")
        self.cancel_button = QPushButton("Zrušit")

        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)

        layout.addWidget(self.save_button)
        layout.addWidget(self.cancel_button)

    def save_settings(self):
        for (section, key), edit in self.fields.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config[section][key] = edit.text()

        with open(self.ini_path, "w") as f:
            self.config.write(f)

        self.accept()
