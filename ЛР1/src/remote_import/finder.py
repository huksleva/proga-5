from importlib.abc import PathEntryFinder
from importlib.util import spec_from_loader

from .loader import URLLoader


class URLFinder(PathEntryFinder):

    def __init__(self, url, available):
        self.url = url
        self.available = available


    def find_spec(self, name, target=None):

        if name in self.available:
            origin = f"{self.url}/{name}.py"

            loader = URLLoader()

            return spec_from_loader(
                name,
                loader,
                origin=origin
            )

        return None