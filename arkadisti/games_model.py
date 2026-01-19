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
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

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
