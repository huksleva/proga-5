import sys

from remote_import import url_hook


sys.path_hooks.append(url_hook)

sys.path_importer_cache.clear()

print(
    "Remote import activated"
)

print(sys.path_hooks)