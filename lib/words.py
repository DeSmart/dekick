"""Reads words.json and returns a list of words"""

import json

from lib.settings import DEKICK_PATH


def get_words() -> list[str]:
    with open(f"{DEKICK_PATH}/lib/words.json", "r", encoding="utf-8") as file:
        words = json.load(file)
        return words
