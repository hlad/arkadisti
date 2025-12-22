import re
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from PySide6.QtCore import Signal

API_URL = "https://hrynehrajeme.cz/wp-json/wp/v2/posts/"
STORE_FILE = "store.h5"


class Scraper:
    progress = Signal(int)

    @staticmethod
    def get_newest():
        response = requests.get(API_URL)
        response.raise_for_status()

        posts = response.json()

        pattern = re.compile(r"hrynehrajeme-arcade-turnaj-(\d+)")

        newest = None
        newest_num = -1

        for post in posts:
            slug = post.get("slug", "")
            match = pattern.fullmatch(slug)
            if match:
                num = int(match.group(1))
                if num > newest_num:
                    newest_num = num
                    newest = post

        return newest

    @staticmethod
    def get_all():
        response = requests.get(API_URL)
        response.raise_for_status()

        posts = response.json()

        pattern = re.compile(r"hrynehrajeme-arcade-turnaj-(\d+)")

        posts_result = {}

        for post in posts:
            slug = post.get("slug", "")
            match = pattern.fullmatch(slug)
            if match:
                round = match.group(1)
                posts_result[round] = post

        return posts_result

    @staticmethod
    def get_rom_names(content):
        soup = BeautifulSoup(content, "html.parser")

        roms = []

        for h3 in soup.find_all("h3"):
            text = h3.get_text(strip=True)
            match = re.search(r"ROM:\s*([a-zA-Z0-9_]+)", text)
            if match:
                roms.append(match.group(1))

        return roms

    @staticmethod
    def scrape_table(content, game):
        soup = BeautifulSoup(content, "html.parser")

        tables = soup.find_all("table")

        target_tables = []

        for table in tables:
            found = False
            for sibling in table.find_previous_siblings():
                if sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    text = sibling.get_text(strip=True)
                    if game in text:
                        found = True
                        break
            if found:
                target_tables.append(table)

        if not target_tables:
            print("No table found for %s." % game)
            return None

        target_table = target_tables[0]

        df = pd.read_html(StringIO(str(target_table)))[0]

        pd.options.mode.copy_on_write = True

        df["Score"] = (
            df["Score"]
            .astype(str)
            .str.replace(r"\D+", "", regex=True)
            .astype(int)
        )

        df = df.drop(columns=['Screenshot', 'INP'])

        avatar_urls = []
        for row in target_table.find_all("tr"):
            img = row.find("img", class_="avatar avatar-32 photo wpat-avatar")
            if img and img.get("src"):
                avatar_urls.append(img["src"])
        df["Avatar"] = avatar_urls

        input_urls = []
        for row in target_table.find_all("tr"):
            all = row.find_all("a", href=True)
            for a in all:
                if a and a.get("href").lower().endswith(".zip"):
                    input_urls.append(a.get("href"))
        df["Input"] = input_urls

        screenshot_urls = []
        for row in target_table.find_all("tr"):
            all = row.find_all("a", href=True)
            for a in all:
                if a and a.get("href").lower().endswith(".png"):
                    screenshot_urls.append(a.get("href"))
        df["Screenshot"] = screenshot_urls

        return df

    @staticmethod
    def download():

        games = []

        store = pd.HDFStore("store.h5", mode="w")

        all = Scraper.get_all()
        for _k, a in all.items():
            roms = Scraper.get_rom_names(a["content"]["rendered"])
            games = games + roms
            for rom in roms:
                df = Scraper.scrape_table(a["content"]["rendered"], rom)
                store[rom] = df
        games_df = pd.DataFrame(games, columns=["games"])
        store["games"] = games_df
        store.close()
