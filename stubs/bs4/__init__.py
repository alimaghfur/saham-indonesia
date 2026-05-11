"""Minimal bs4 stub for import testing."""


class BeautifulSoup:
    def __init__(self, markup='', features=None, **kwargs):
        self.markup = markup

    def find(self, *args, **kwargs):
        return None

    def find_all(self, *args, **kwargs):
        return []

    def select(self, *args, **kwargs):
        return []
