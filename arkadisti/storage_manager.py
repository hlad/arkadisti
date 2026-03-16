import pandas as pd

STORE_FILE = "store.h5"


class StorageManager:
    def __init__(self):
        self.store = pd.HDFStore(STORE_FILE)

    def get_results(self, game):
        return self.store[game]

    def get_games(self):
        return self.store["games"]

    def set_game(self, game, data):
        self.store[game] = data

    def set_games(self, games):
        self.store["games"] = games
