import requests


class URLLoader:
    def create_module(self, spec):
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

        source = response.text

        code = compile(
            source,
            url,
            mode="exec",
        )

        exec(
            code,
            module.__dict__,
        )
