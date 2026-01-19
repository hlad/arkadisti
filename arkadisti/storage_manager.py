import pandas as pd

STORE_FILE = "store.h5"


class StorageManager:
    def __init__(self):
        self.store = pd.HDFStore(STORE_FILE)

    def get_results(self, game):
        return self.store[game]

    def get_games(self):
        return self.store["games"]
