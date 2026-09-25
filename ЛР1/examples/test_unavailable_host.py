import sys

from remote_import import url_hook


sys.path_hooks.append(url_hook)
sys.path.append("http://localhost:9999")
sys.path_importer_cache.clear()

try:
    import some_remote_module
except ImportError as exc:
    print("Import error handled:")
    print(exc)
