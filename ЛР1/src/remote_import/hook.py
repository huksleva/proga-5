from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse

import requests

from .finder import URLFinder


_hook_active = False


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attributes = dict(attrs)
            href = attributes.get("href")

            if href:
                self.links.append(href)


def get_links(url):
    response = requests.get(url, timeout=5)
    response.raise_for_status()

    parser = LinkParser()
    parser.feed(response.text)

    return parser.links


def get_name(href):
    path = urlparse(href).path.rstrip("/")

    if not path:
        return ""

    return unquote(path.split("/")[-1])


def is_valid_name(name):
    if not name:
        return False

    if not (name[0].isalpha() or name[0] == "_"):
        return False

    return all(
        char.isalnum() or char == "_"
        for char in name
    )


def url_hook(path):
    global _hook_active

    if not path.startswith(("http://", "https://")):
        raise ImportError

    if _hook_active:
        raise ImportError

    _hook_active = True

    try:
        base_url = path.rstrip("/") + "/"

        try:
            links = get_links(base_url)
        except requests.RequestException as exc:
            raise ImportError(
                f"Host unavailable: {base_url}"
            ) from exc

        modules = set()
        packages = set()

        for href in links:
            name = get_name(href)

            if href.endswith("/") and is_valid_name(name):
                package_url = urljoin(base_url, f"{name}/")

                try:
                    package_links = get_links(package_url)
                except requests.RequestException:
                    continue

                package_files = {
                    get_name(package_href)
                    for package_href in package_links
                }

                if "__init__.py" in package_files:
                    packages.add(name)

            elif name.endswith(".py"):
                module_name = name[:-3]

                if is_valid_name(module_name):
                    modules.add(module_name)

        return URLFinder(
            base_url,
            modules,
            packages,
        )

    finally:
        _hook_active = False