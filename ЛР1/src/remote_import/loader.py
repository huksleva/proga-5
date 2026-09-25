import requests


class URLLoader:
    def create_module(self, spec):
        # None поручает Python создать объект модуля стандартным способом.
        return None

    def exec_module(self, module):
        url = module.__spec__.origin

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ImportError(
                f"Unable to load remote module: {url}"
            ) from exc

        # compile() принимает bytes и сам учитывает объявленную кодировку файла.
        source = response.content

        # URL передаётся как имя файла, чтобы он отображался в traceback.
        code = compile(
            source,
            url,
            mode="exec",
        )

        # Код выполняется непосредственно в пространстве имён нового модуля.
        exec(
            code,
            module.__dict__,
        )
