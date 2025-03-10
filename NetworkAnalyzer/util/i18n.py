# i18n = Internatianalization module

import json


class I18N:
    def __init__(self, language):
        self.language = language
        self.strings = self.load_strings()

    def load_strings(self):
        file_path = f"langs/{self.language}.json"
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise Exception(f"Language file {file_path} not found.")

    def get(self, key):
        return self.strings.get(key, key)
