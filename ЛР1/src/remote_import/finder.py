from importlib.abc import PathEntryFinder
from importlib.util import spec_from_loader

from .loader import URLLoader


class URLFinder(PathEntryFinder):
    def __init__(self, url, available, packages, unavailable_error=None):
        self.url = url.rstrip("/") + "/"
        self.available = set(available)
        self.packages = set(packages)
        self.unavailable_error = unavailable_error

    def find_spec(self, fullname, target=None):
        if self.unavailable_error is not None:
            raise ImportError(
                f"Host unavailable: {self.url}"
            ) from self.unavailable_error

        # Для вложенного имени package.module нужен только последний компонент.
        name = fullname.rsplit(".", 1)[-1]

        if name in self.available:
            origin = f"{self.url}{name}.py"

            return spec_from_loader(
                fullname,
                URLLoader(),
                origin=origin,
            )

        if name in self.packages:
            package_url = f"{self.url}{name}/"
            origin = f"{package_url}__init__.py"

            spec = spec_from_loader(
                fullname,
                URLLoader(),
                origin=origin,
                is_package=True,
            )

            # По этому URL Python будет искать дочерние модули пакета.
            spec.submodule_search_locations = [package_url]

            return spec

        return None
