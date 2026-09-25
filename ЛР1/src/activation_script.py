import sys

from remote_import import url_hook


# После регистрации HTTP/HTTPS-адреса в sys.path сможет обработать url_hook.
sys.path_hooks.append(url_hook)
# Удаляем ранее выбранные импортёры, чтобы Python применил новый hook.
sys.path_importer_cache.clear()

print("Remote import activated")
print(sys.path_hooks)
