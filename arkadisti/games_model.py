import pandas as pd
from PySide6.QtCore import QAbstractListModel, Qt

STORE_FILE = "store.h5"


class GamesModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        store = pd.HDFStore(STORE_FILE)
        if "games" in store:
            self._data = store["games"]
        else:
            self._data = pd.DataFrame()
        store.close()

        self.beginResetModel()
        self.endResetModel()

    def data(self, index, role):
        row = index.row()

        if row < 0 or row >= len(self._data):
            return None

        if not isinstance(row, int):
            return None

        if role == Qt.DisplayRole:
            name = self._data.loc[row, "name"]
            return name
        elif role == Qt.UserRole:
            game = self._data.loc[row, "games"]
            return game
        elif role == Qt.UserRole+1:
            tournament_id = self._data.loc[row, "tournament_id"]
            return tournament_id
        elif role == Qt.UserRole+2:
            method = self._data.loc[row, "method"]
            return method
        elif role == Qt.UserRole+3:
            action = self._data.loc[row, "action"]
            return action
        return None

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def reload(self):
        self.beginResetModel()

        with pd.HDFStore(STORE_FILE) as store:
            if "games" in store:
                self._data = store["games"]
            else:
                self._data = pd.DataFrame()

        self.endResetModel()
