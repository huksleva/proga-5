import re
import requests

from .finder import URLFinder


def url_hook(path):

    if not path.startswith(
        ("http://", "https://")
    ):
        raise ImportError


    try:
        response = requests.get(
            path,
            timeout=5
        )

        response.raise_for_status()

    except requests.RequestException:

        raise ImportError(
            f"Host unavailable: {path}"
        )


    filenames = re.findall(
        r"[a-zA-Z_][a-zA-Z0-9_]*\.py",
        response.text
    )


    modules = {
        name[:-3]
        for name in filenames
    }


    return URLFinder(
        path.rstrip("/"),
        modules
    )