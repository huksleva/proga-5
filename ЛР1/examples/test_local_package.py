import sys

from remote_import import url_hook

sys.path_hooks.append(url_hook)
sys.path.append("http://localhost:8000")
sys.path_importer_cache.clear()

import remote_package

print(remote_package.add(2, 3))
print(remote_package.multiply(4, 5))
print(remote_package.hello("student"))