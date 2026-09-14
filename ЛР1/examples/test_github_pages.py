import sys

REMOTE_URL = "https://github.com/huksleva/proga-5"

sys.path.append(REMOTE_URL)
sys.path_importer_cache.clear()

import remote_package

print(remote_package.add(10, 20))
print(remote_package.multiply(6, 7))
print(remote_package.hello("GitHub Pages"))
