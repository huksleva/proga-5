import sys

from remote_import import url_hook


sys.path_hooks.append(url_hook)
sys.path.append("http://localhost:8000")
sys.path_importer_cache.clear()

import myremotemodule

myremotemodule.myfoo()
