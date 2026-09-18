# Лабораторная работа 2

## Исследование пакетов

| Пакет | Наблюдения | Применение в проекте |
| --- | --- | --- |
| [requests](https://pypi.org/project/requests/) | Публичный HTTP API, сессии, документация, лицензия, зависимости и ограничения версий Python; опубликованы wheel и sdist. | Повторное использование сессии, таймаут, README и метаданные пакета. |
| [yandex-weather-api](https://pypi.org/project/yandex-weather-api/) | Тонкая обёртка над JSON погодного API, внедрение сессии, CLI; есть wheel и sdist и ссылка на исходники. | Сохранение JSON-ответа, внедрение сессии для тестов, консольная команда. |

Страница указанного в задании python-open-weather не была доступна при
проверке, поэтому утверждения о его устройстве в отчёт не включены.

## Реализация

Исходный погодный проект отсутствовал, поэтому создан новый пакет
`huksleva-openweather`. Использована структура `src`, декларативные метаданные
в `pyproject.toml`, MIT-лицензия, публичный API и маркер типов `py.typed`.
Тесты проверяют параметры запросов, ошибки сервера, таймауты, некорректные
ответы и владение сессией. Ключ API читается из окружения и не записывается
в исходники. Настроен GitHub Actions для Python 3.10–3.14 на Linux и Windows.
Наличие конфигурации CI не означает, что все эти версии уже проверены.

Подход к сборке актуализирован по
[Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
Из [статьи об идеальном пакете](https://habr.com/ru/articles/483512/)
взяты разделение исходников и тестов и проверки на нескольких версиях Python.
Процесс публикации описан в
[инструкции из задания](https://proglib.io/p/kak-opublikovat-svoyu-python-biblioteku-na-pypi-2020-01-28)
и разделе Development and Publication ниже.

## Публикация и результаты проверки

Локально на Python 3.13 успешно выполнены 8 тестов, сборка sdist и wheel,
проверка обоих архивов через `twine check` и установка готового wheel в `.venv`.
Реальные запросы к OpenWeather без пользовательского API-ключа не проверялись.

Публикация ещё не выполнена: требуется доступ к аккаунту TestPyPI.
После успешной загрузки сюда нужно добавить подтверждённую ссылку на пакет.
В описании и метаданных уже указана ссылка на
[GitHub-репозиторий](https://github.com/huksleva/proga-5).

# huksleva-openweather

Python client for OpenWeather current weather and five-day forecasts.
Supports Python 3.10+ and exposes a library API and a command-line interface.

Source repository: [huksleva/proga-5](https://github.com/huksleva/proga-5).
Package sources are in the `ЛР2` directory. Licensed under MIT.

## Installation

After publication to TestPyPI, install the dependency from PyPI and the package
from TestPyPI separately:

```console
python -m pip install "requests>=2.32,<3"
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps huksleva-openweather
```

## Library

Create an API key in your OpenWeather account and set `OPENWEATHER_API_KEY`.

```python
import os
from huksleva_openweather import OpenWeatherClient, OpenWeatherError

try:
    with OpenWeatherClient(os.environ["OPENWEATHER_API_KEY"]) as client:
        weather = client.current("Moscow,RU")
        print(weather["main"]["temp"])
        forecast = client.forecast("Moscow,RU")
except OpenWeatherError as exc:
    print(exc)
```

Responses retain the OpenWeather JSON structure. Units can be `metric`,
`imperial`, or `standard`; the default language is `ru`. The default request
timeout is ten seconds. HTTP, transport, and malformed-response errors raise
`OpenWeatherError`; invalid arguments raise `ValueError`.

## CLI

```console
huksleva-weather "Moscow,RU"
huksleva-weather "Moscow,RU" --forecast --units metric --lang en
```

## Development and Publication

Run these commands from the package directory:

```console
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip install build twine
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

Twine asks for username `__token__` and a TestPyPI API token as the password.
TestPyPI uses a separate account from PyPI. Do not commit credentials.
The intended project URL is https://test.pypi.org/project/huksleva-openweather/;
this URL is valid only after a successful upload.
