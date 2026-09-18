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
и разделе «Разработка и публикация» ниже.

## Публикация и результаты проверки

Локально на Python 3.13 успешно выполнены 8 тестов, сборка sdist и wheel,
проверка обоих архивов через `twine check` и установка готового wheel в `.venv`.
Реальные запросы к OpenWeather без пользовательского API-ключа не проверялись.

Пакет `huksleva-openweather` версии `0.1.0` опубликован в TestPyPI:
[ссылка на опубликованный пакет для сдачи ЛР](https://test.pypi.org/project/huksleva-openweather/0.1.0/).
Наличие релиза и ссылки на исходники проверено через публичный API TestPyPI.
В опубликованном описании и метаданных указана ссылка на
[GitHub-репозиторий](https://github.com/huksleva/proga-5).

# huksleva-openweather

Клиент OpenWeather для получения текущей погоды и прогноза на пять дней.
Поддерживает Python 3.10 и новее. Доступен как библиотека и консольная команда.

Репозиторий исходного кода: [huksleva/proga-5](https://github.com/huksleva/proga-5).
Исходники пакета находятся в папке `ЛР2`. Лицензия: MIT.

## Установка

Установите зависимость из PyPI, а сам пакет из TestPyPI:

```console
python -m pip install "requests>=2.32,<3"
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps huksleva-openweather==0.1.0
```

## Использование библиотеки

Создайте ключ API в аккаунте OpenWeather и задайте переменную окружения
`OPENWEATHER_API_KEY`. В PowerShell:

```powershell
$env:OPENWEATHER_API_KEY = "ваш-ключ-OpenWeather"
```

Пример получения погоды и прогноза:

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

Ответы сохраняют структуру JSON OpenWeather. Единицы измерения: `metric`
(градусы Цельсия), `imperial` (градусы Фаренгейта) или `standard` (кельвины).
По умолчанию используются `metric` и язык `ru`. Таймаут запроса: десять секунд.
Ошибки HTTP, соединения и формата ответа вызывают `OpenWeatherError`,
некорректные аргументы вызывают `ValueError`.

## Командная строка

```console
huksleva-weather "Moscow,RU"
huksleva-weather "Moscow,RU" --forecast --units metric --lang en
```

## Разработка и публикация

### 1. Разместите исходники на GitHub

Закоммитьте файлы проекта и отправьте изменения в
[репозиторий](https://github.com/huksleva/proga-5), чтобы преподаватель мог
просмотреть код. Папки `.venv`, `dist`, `build` и `*.egg-info` уже исключены
из Git через `.gitignore`.

### 2. Подготовьте аккаунт TestPyPI

Зарегистрируйтесь на [TestPyPI](https://test.pypi.org/account/register/),
подтвердите адрес электронной почты и настройте двухфакторную аутентификацию,
если сайт её запрашивает. Это отдельный аккаунт, независимый от PyPI.
В [настройках аккаунта](https://test.pypi.org/manage/account/) создайте API-токен.
Для первой публикации выберите область действия «Entire account»:
проект ещё не создан. Токен используется как пароль Twine; не записывайте
его в репозиторий и не отправляйте в чат.

### 3. Проверьте и заново соберите пакет

Откройте PowerShell. Команды используют Python из `.venv` напрямую,
поэтому активировать окружение не требуется:

```powershell
Set-Location "C:\Leo\projects\proga-5\ЛР2"
.\.venv\Scripts\python.exe -m pip install -e . build twine
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe -m twine check dist/*
```

Сборку нужно повторить после изменения README: его содержимое включается
в архивы и отображается на странице пакета.

### 4. Загрузите пакет

```powershell
.\.venv\Scripts\python.exe -m twine upload --repository testpypi --username __token__ dist/huksleva_openweather-0.1.0*
```

Когда Twine запросит пароль, вставьте API-токен TestPyPI целиком, включая
префикс `pypi-`. При вводе пароль не отображается. Ключ OpenWeather для
публикации не нужен.

После успешной загрузки проверьте
[страницу пакета](https://test.pypi.org/project/huksleva-openweather/):
описание должно содержать этот README и ссылку на GitHub.
Версия `0.1.0` уже опубликована. Команда выше приведена как пример первой
публикации; для обновления используйте новую версию, как описано ниже.

Если имя занято другим пользователем, измените `name` в `pyproject.toml`
на уникальное и обновите имя в командах и ссылках README.
Для следующего релиза увеличьте `version`, например до `0.1.1`, заново
соберите пакет и загружайте только архивы новой версии. Повторно загрузить
тот же файл опубликованного релиза нельзя.

### 5. Оформите результат ЛР

Факт публикации и ссылка на пакет указаны в разделе
«Публикация и результаты проверки». Отправьте обновлённый README на GitHub.
В ответ на задание приведите
[ссылку на версию 0.1.0 в TestPyPI](https://test.pypi.org/project/huksleva-openweather/0.1.0/).

Изменения README на GitHub не меняют описание уже опубликованной версии
в TestPyPI: для обновления описания потребуется новый релиз.

Инструкция основана на
[официальном руководстве по упаковке Python-проектов](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
