import sys

sys.path.append("http://localhost:9999")
sys.path_importer_cache.clear()

try:
    import some_remote_module
except ImportError as exc:
    print("Import error handled:")
    print(exc)
