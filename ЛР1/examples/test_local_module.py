import sys

sys.path.append("http://localhost:8000")
sys.path_importer_cache.clear()

import myremotemodule

myremotemodule.myfoo()
