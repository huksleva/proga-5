import requests
import sys

from remote_import import url_hook


REMOTE_URL = "https://huksleva.github.io/proga-5/"


sys.path_hooks.insert(0, url_hook)
sys.path.insert(0, REMOTE_URL)
sys.path_importer_cache.clear()


import remote_package


print(remote_package.add(10, 20))
print(remote_package.multiply(6, 7))
print(remote_package.hello("GitHub Pages"))