import configparser
import platform
from pathlib import Path

from PySide6.QtCore import QObject

CONFIG_FILE = "settings.ini"


class ConfigManager(QObject):
    def __init__(self):
        self.config = configparser.ConfigParser()

        self.config_file = Path(CONFIG_FILE)

        if not self.config_file.exists():
            self.create_config()
        else:
            self.read_config()

    def create_config(self):
        # self.config = configparser.ConfigParser()

        # config_file = Path(CONFIG_FILE)

        system = platform.system().lower()
        if system == "windows":
            mame_bin = "mame.exe"
        elif system == "darwin":
            mame_bin = "mame"
        else:
            mame_bin = "mame"

        roms_dir = str(Path("roms"))
        inp_dir = str(Path("inp"))
        snap_dir = str(Path("snap"))
        output_dir = str(Path("output"))

        self.config["general"] = {
            "mame_binary": mame_bin,
            "roms_dir": roms_dir,
            "inp_dir": inp_dir,
            "snap_dir": snap_dir,
            "output_dir": output_dir,
        }

        # with config_file.open(
        #     mode="w", encoding="utf-8"
        # ) as config_file_handle:
        #     self.config.write(config_file_handle)
        self.save_config()

        Path(self.get_output_dir()).mkdir(parents=True, exist_ok=True)

    def read_config(self):
        config_file = Path(CONFIG_FILE)
        self.config.read(config_file)

    def save_config(self):
        with self.config_file.open(
            mode="w", encoding="utf-8"
        ) as config_file_handle:
            self.config.write(config_file_handle)

    def get_roms_dir(self):
        return Path(self.config.get("general", "roms_dir"))

    def get_inp_dir(self):
        return Path(self.config.get("general", "inp_dir"))

    def get_snap_dir(self):
        return Path(self.config.get("general", "snap_dir"))

    def get_output_dir(self):
        return Path(self.config.get("general", "output_dir"))

    def get_mame_binary(self):
        return Path(self.config.get("general", "mame_binary"))
