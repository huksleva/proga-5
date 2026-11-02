# Отчёт по ЛР3: Protocol Buffers и gRPC, микросервисы Recommendations + Marketplace

Сформирован автоматически скриптом `run_lab.py`: 2026-11-02 14:00:31, Windows-10-10.0.19045-SP0, Python 3.13.2.

Все выводы ниже — реальные, получены при локальном запуске. Подробный порядок развёртывания — в [README.md](README.md).

## Итоги прогона

| Шаг | Результат |
|---|---|
| Версии окружения | OK |
| Генерация кода protoc | OK |
| Часть 1: protobuf без gRPC | OK |
| Часть 2: байты и эволюция схемы | OK |
| Hello World: клиент | OK |
| Hello World: ошибка типа аргумента | OK |
| Потоковые вызовы gRPC | OK |
| Ошибки, дедлайны, метаданные, grpc.aio | OK |
| Микросервисы: оба сервиса запущены локально | OK |
| Marketplace: REST API → gRPC | OK |
| Marketplace: валидация (422) | OK |
| Marketplace: HTML-страница | OK |
| pytest: Recommendations | OK |
| pytest: Marketplace (интеграционные) | OK |
| Marketplace: 503 при недоступном Recommendations | OK |
| docker compose up --build -d | OK |
| docker compose ps | OK |
| Docker: Marketplace → Recommendations | OK |
| Docker: pytest в контейнере recommendations | OK |
| Docker: pytest в контейнере marketplace | OK |
| docker compose logs | OK |
| docker compose down | OK |
> Порт 8000 на этом компьютере недоступен (занят или зарезервирован системой), поэтому Marketplace работает на порту **8888** (`MARKETPLACE_PORT`).


## 0. Окружение

Работа выполняется локально в виртуальном окружении (`python -m venv .venv`), зависимости — из `pyproject.toml` (раздел «Подготовка окружения» ноутбука, `%pip install` заменён на `pip install .`).

Команда:

```shell
$ python env_info.py
```

Вывод:

```text
ОС:         Windows-10-10.0.19045-SP0
Python:     3.13.2
grpcio:     1.85.1
protobuf:   7.36.2
fastapi:    0.162.0
uvicorn:    0.54.0

[2.4 с]
```


## 1. Генерация кода из .proto

Компилятор `protoc` запускается как модуль `grpc_tools.protoc` (пакет `grpcio-tools`). Ключ `-I protos` задаёт корень поиска, поэтому путь Python-модуля повторяет путь `.proto`-файла (`library.v1.library_pb2`), а не директиву `package`.

Команда:

```shell
$ python generate.py
```

Вывод:

```text
$ python -m grpc_tools.protoc -I protos --python_out=. --pyi_out=. protos/library/v1/library.proto protos/encoding_demo.proto protos/evolution/v1/user.proto protos/evolution/v2/user.proto
$ python -m grpc_tools.protoc -I protos --python_out=. --pyi_out=. --grpc_python_out=. protos/helloworld.proto protos/stats.proto protos/library/v1/library_service.proto
$ python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=. --grpc_python_out=. ../protos/recommendations.proto
$ python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=. --grpc_python_out=. ../protos/recommendations.proto
Готово.

[2.2 с]
```

Команда:

```shell
$ ls *_pb2*.py  # сгенерированные файлы
```

Вывод:

```text
encoding_demo_pb2.py
evolution/v1/user_pb2.py
evolution/v2/user_pb2.py
helloworld_pb2.py
helloworld_pb2_grpc.py
library/v1/library_pb2.py
library/v1/library_service_pb2.py
library/v1/library_service_pb2_grpc.py
microservices/marketplace/recommendations_pb2.py
microservices/marketplace/recommendations_pb2_grpc.py
microservices/recommendations/recommendations_pb2.py
microservices/recommendations/recommendations_pb2_grpc.py
stats_pb2.py
stats_pb2_grpc.py
```


## 2. Часть 1–2. Protocol Buffers без gRPC и устройство байтов

Сообщения, сериализация, сравнение с JSON, значения по умолчанию, `oneof` (часть 1); ручной разбор wire format, varint/zigzag и эволюция схемы (часть 2). Последняя строка варианта «a = 300» — упражнение 2 для самопроверки.

Команда:

```shell
$ python part1_protobuf.py
```

Вывод:

```text

=== 1.3 Создаём сообщение ===
id: 1
title: "Solaris"
authors {
  name: "Stanisław Lem"
  birth_year: 1921
}
genre: GENRE_FICTION
attributes {
  key: "publisher"
  value: "MON"
}
attributes {
  key: "language"
  value: "pl"
}
published_at {
  seconds: -283996800
}
isbn: "978-0-15-602760-1"


=== 1.4 Сериализация и разбор ===
bytes 100 байт
08 01 12 07 53 6f 6c 61 72 69 73 1a 13 0a 0e 53 74 61 6e 69 73 c5 82 61 77 20 4c 65 6d 10 81 0f 20 01 2a 10 0a 09 70 75 62 6c 69 73 68 65 72 12 03 4d 4f 4e 2a 0e 0a 08 6c 61 6e 67 75 61 67 65 12 02 70 6c 32 0b 08 80 9b ca f8 fe ff ff ff ff 01 3a 11 39 37 38 2d 30 2d 31 35 2d 36 30 32 37 36 30 2d 31
Объекты равны: True
Заголовок после разбора: Solaris

=== 1.5 Сравнение с JSON ===
{"id": "1", "title": "Solaris", "authors": [{"name": "Stanis\u0142aw Lem", "birthYear": 1921}], "genre": "GENRE_FICTION", "attributes": {"language": "pl", "publisher": "MON"}, "publishedAt": "1961-01-01T00:00:00Z", "isbn": "978-0-15-602760-1"}

JSON:     243 байт
protobuf: 100 байт
1961-01-01T00:00:00Z

Каталог из 1000 книг:
protobuf:   49566 байт
JSON:      152597 байт  (в 3.1 раза больше)
Сериализация: protobuf 0.428 мс, json 2.637 мс
Разбор:       protobuf 1.264 мс, json 2.873 мс

=== 1.6 Значения по умолчанию и наличие поля ===
'' 0 0 [] {}
Пустое сообщение занимает 0 байт
published_at задано? False
birth_year задано? False
birth_year задано после присваивания 0? True
ValueError: Field library.v1.Book.title does not have presence.

=== 1.7 oneof и проверка типов ===
Задано: isbn
Задано: ebook_url | isbn теперь: ''
                      '1' → TypeError: 'str' object cannot be interpreted as an integer
   1180591620717411303424 → ValueError: Value out of range: 1180591620717411303424
                      1.5 → TypeError: 'float' object cannot be interpreted as an integer
TypeError: Fail to convert to Timestamp. Expected a datetime object got Timestamp
1970-01-01 00:00:00

[1.9 с]
```

Команда:

```shell
$ python part2_bytes.py
```

Вывод:

```text

=== 2.1 Разбираем сообщение вручную ===
поле  1  VARINT  1
поле  2  LEN     b'Solaris'
поле  3  LEN     b'\n\x0eStanis\xc5\x82aw Lem\x10\x81\x0f'
поле  4  VARINT  1
поле  5  LEN     b'\n\tpublisher\x12\x03MON'
поле  5  LEN     b'\n\x08language\x12\x02pl'
поле  6  LEN     b'\x08\x80\x9b\xca\xf8\xfe\xff\xff\xff\xff\x01'
поле  7  LEN     b'978-0-15-602760-1'
Вложенное сообщение автора:
  поле  1  LEN     b'Stanis\xc5\x82aw Lem'
  поле  2  VARINT  1921

=== 2.2 Varint, zigzag и упакованные списки ===
a = 150                   3 байт: 08 96 01
b = 'testing'             9 байт: 12 07 74 65 73 74 69 6e 67
negative = -1 (int32)    11 байт: 18 ff ff ff ff ff ff ff ff ff 01
zigzag = -1 (sint32)      2 байт: 20 01
zigzag = 1 (sint32)       2 байт: 20 02
nums = [1, 2, 300]        6 байт: 2a 04 01 02 ac 02
a = 300 (упражнение 2)    3 байт: 08 ac 02

=== 2.3 Эволюция схемы ===
v1 читает данные v2: 'id: 1\nname: "Ann"\n'
email старому коду неизвестен, но сохранён: True
После пересылки через старый код: 'id: 1\nname: "Ann"\nemail: "ann@example.com"\n'
v2 читает данные v1: 'id: 2\nname: "Bob"\n' email = ''
Несовместимое изменение типа: id = 3 | name = 0 (ошибки нет, данные потеряны)

[0.3 с]
```


## 3. Часть 3. Первый gRPC-сервис: Hello World

Контракт `protos/helloworld.proto` содержит `SayHello`, `SayHelloAgain`, `SayMyName` (п. 3.4) и `SayGoodbye` (упражнение 1). Сервер запускается отдельным процессом, затем вызывается клиент.

Команда:

```shell
$ python greeter_client.py
```

Вывод:

```text
Will try to greet world ...
Greeter client received: Hello, you!
Greeter client received: Hello again, you!
— You're Heisenberg.
— You're goddamn right.
Greeter client received: Goodbye, you!

[0.7 с]
```

**Ошибка типа аргумента.** В `SayMyName` передано сообщение *ответа* вместо *запроса*. Вызов «случайно» работает: в двоичном сообщении нет имени типа, а у обоих сообщений поле 1 — строка.

Команда:

```shell
$ python wrong_type_client.py
```

Вывод:

```text
— You're Heisenberg.
— You're goddamn right.
Вызов сработал: у MyNameReply и MyNameRequest поле 1 — строка, байты совпадают.

[0.7 с]
```

Команда:

```shell
$ # вывод сервера greeter_server.py
```

Вывод:

```text
Server started, listening on 50051
```


## 4. Часть 4. Потоковые вызовы

Серверный поток (`Countdown`), клиентский (`Sum`) и двунаправленный (`RunningAverage`), отмена потока клиентом и `INVALID_ARGUMENT`.

Команда:

```shell
$ python stats_demo.py
```

Вывод:

```text
Сервер Stats запущен

--- Серверный поток: Countdown(5) ---
 0.0 с: 5
 0.2 с: 4
 0.4 с: 3
 0.6 с: 2
 0.8 с: 1
 1.0 с: 0

--- Клиентский поток: Sum ---
Сумма 16.5 из 4 чисел

--- Двунаправленный поток: RunningAverage ---
  → отправляем 10
  ← среднее после 1 чисел: 10.0
  → отправляем 20
  ← среднее после 2 чисел: 15.0
  → отправляем 30
  ← среднее после 3 чисел: 20.0
  → отправляем 40
  ← среднее после 4 чисел: 25.0

--- Отмена потока клиентом и INVALID_ARGUMENT ---
20 19 18 17 
Вызов завершён: StatusCode.CANCELLED
Ошибка: StatusCode.INVALID_ARGUMENT — start must be >= 0
Сервер Stats остановлен
Countdown: клиент отключился

[3.9 с]
```


## 5. Часть 5. Ошибки, дедлайны, метаданные, grpc.aio

`LibraryService`: метаданные запроса и ответа, коды статуса (`NOT_FOUND`, `INVALID_ARGUMENT`, `UNAUTHENTICATED`, `DEADLINE_EXCEEDED`), асинхронный клиент `grpc.aio` и server reflection (то, что делает `grpcurl list`).

Команда:

```shell
$ python library_demo.py
```

Вывод:

```text
Сервер LibraryService запущен

--- 5.1 Метаданные ---
Solaris — Stanisław Lem
Метаданные ответа: {'x-request-id': 'req-42', 'x-served-by': 'library-1'}

--- 5.2 Коды статуса ---
id=2: A Brief History of Time
id=999: NOT_FOUND — Book 999 not found
id=0: INVALID_ARGUMENT — id must be positive
1 Solaris
4 Roadside Picnic

--- 5.3 Аутентификация через метаданные и дедлайны ---
без токена          0.0 с  UNAUTHENTICATED — Missing or invalid token
короткий дедлайн    0.5 с  DEADLINE_EXCEEDED — Deadline Exceeded
BuildReport: клиент больше не ждёт, прекращаем работу
успех               1.0 с  OK: 4 книги, {'GENRE_SCIENCE': 1, 'GENRE_HISTORY': 1, 'GENRE_FICTION': 2}

--- 5.4 Асинхронный клиент grpc.aio ---
id=1: Solaris
id=2: A Brief History of Time
id=3: The Guns of August
id=4: Roadside Picnic
id=42: NOT_FOUND

--- 5.5 Server reflection (аналог grpcurl list) ---
grpc.reflection.v1alpha.ServerReflection
library.v1.LibraryService

Сервер LibraryService остановлен

[2.4 с]
```


## 6. Часть 6. Микросервисы Recommendations и Marketplace (локально)

```
Браузер / curl --HTTP, REST, JSON--> Marketplace (FastAPI, :8000)
                                          | gRPC, Protobuf
                                          v
                                     Recommendations (:50051)
```

Контракт `microservices/protos/recommendations.proto` общий; код из него генерируется в каталог каждого сервиса (это уже сделано на шаге 1).

Оба сервиса запущены отдельными процессами. Документация OpenAPI: http://127.0.0.1:8888/docs.

Команда:

```shell
$ GET http://127.0.0.1:8888/api/v1/recommendations?user_id=1&category=science_fiction&max_results=2
```

Вывод:

```text
HTTP 200
[
  {
    "id": 8,
    "title": "Solaris"
  },
  {
    "id": 5,
    "title": "The Hitchhiker's Guide to the Galaxy"
  }
]
```

Валидация FastAPI: `max_results=50` вне диапазона 1..10 → 422.

Команда:

```shell
$ GET http://127.0.0.1:8888/api/v1/recommendations?user_id=1&max_results=50
```

Вывод:

```text
HTTP 422
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "query",
        "max_results"
      ],
      "msg": "Input should be less than or equal to 10",
      "input": "50",
      "ctx": {
        "le": 10
      }
    }
  ]
}
```

Команда:

```shell
$ GET http://127.0.0.1:8888/
```

Вывод:

```text
HTTP 200
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Online Books For You</title>
  </head>
  <body>
    <h1>Mystery books you may like</h1>
    <ul>
      <li>Murder on the Orient Express</li>
      <li>The Maltese Falcon</li>
      <li>The Name of the Rose</li>
    </ul>
  </body>
</html>
```

Команда:

```shell
$ GET http://127.0.0.1:8888/openapi.json  # пути OpenAPI
```

Вывод:

```text
GET /api/v1/recommendations
```

Модульные тесты Recommendations и интеграционные тесты Marketplace:

Команда:

```shell
$ python -m pytest -q
```

Вывод:

```text
.....                                                                    [100%]
5 passed in 0.28s

[2.1 с]
```

Команда:

```shell
$ python -m pytest -q test_marketplace_integration.py
```

Вывод:

```text
..                                                                       [100%]
2 passed in 0.20s

[1.4 с]
```

**Отказ зависимости.** Останавливаем Recommendations: Marketplace не падает, а возвращает 503.

Команда:

```shell
$ GET http://127.0.0.1:8888/api/v1/recommendations?user_id=1
```

Вывод:

```text
HTTP 503
{
  "detail": "Recommendations service is unavailable"
}
```

Команда:

```shell
$ # вывод Recommendations
```

Вывод:

```text
Recommendations service listening on 50051
```

Команда:

```shell
$ # вывод Marketplace (uvicorn)
```

Вывод:

```text
INFO:     Started server process [11100]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8888 (Press CTRL+C to quit)
INFO:     127.0.0.1:9920 - "GET /api/v1/recommendations?user_id=1&category=science_fiction&max_results=2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:9922 - "GET /api/v1/recommendations?user_id=1&max_results=50 HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:9923 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:9924 - "GET /openapi.json HTTP/1.1" 200 OK
INFO:     127.0.0.1:9933 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:9934 - "GET /api/v1/recommendations?user_id=1&category=science_fiction&max_results=2 HTTP/1.1" 200 OK
INFO:     127.0.0.1:9936 - "GET /api/v1/recommendations?user_id=1 HTTP/1.1" 503 Service Unavailable
```


## 7. Часть 6.4–6.5. Контейнеризация и Docker Compose

Каждый сервис — отдельный образ (`microservices/*/Dockerfile`), контекст сборки — каталог `microservices/`, код из `.proto` генерируется внутри образа. `compose.yaml` описывает обе службы; сеть создаётся автоматически, Marketplace обращается к Recommendations по имени службы (`RECOMMENDATIONS_HOST=recommendations`). Порт Recommendations наружу не публикуется.

Команда:

```shell
$ docker compose up --build -d
```

Вывод:

```text
#1 [internal] load local bake definitions
#1 reading from stdin 1.09kB 0.1s done
#1 DONE 0.1s

#2 [recommendations internal] load build definition from Dockerfile
#2 transferring dockerfile: 423B 0.0s done
#2 DONE 0.0s

#3 [marketplace internal] load build definition from Dockerfile
#3 transferring dockerfile: 447B 0.0s done
#3 DONE 0.1s

#4 [auth] library/python:pull token for registry-1.docker.io
#4 DONE 0.0s

#5 [marketplace internal] load metadata for docker.io/library/python:3.12-slim
#5 DONE 2.5s

#6 [recommendations internal] load .dockerignore
#6 transferring context: 114B 0.0s done
#6 DONE 0.0s

#7 [marketplace 1/7] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#7 DONE 0.0s

#8 [marketplace internal] load build context
#8 transferring context: 305B 0.0s done
#8 DONE 0.0s

#9 [recommendations internal] load build context
#9 transferring context: 321B 0.0s done
#9 DONE 0.0s

#10 [recommendations 4/7] RUN pip install --no-cache-dir -r requirements.txt
#10 CACHED

#11 [recommendations 6/7] COPY recommendations/ .
#11 CACHED

#12 [recommendations 5/7] COPY protos/ /service/protos/
#12 CACHED

#13 [recommendations 3/7] COPY recommendations/requirements.txt .
#13 CACHED

#14 [recommendations 2/7] WORKDIR /service/recommendations
#14 CACHED

#15 [marketplace 5/7] COPY protos/ /service/protos/
#15 CACHED

#16 [marketplace 2/7] WORKDIR /service/marketplace
#16 CACHED

#17 [marketplace 6/7] COPY marketplace/ .
#17 CACHED

#18 [marketplace 3/7] COPY marketplace/requirements.txt .
#18 CACHED

#19 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#19 CACHED

#20 [recommendations 7/7] RUN python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=.     --grpc_python_out=. ../protos/recommendations.proto
#20 CACHED

#21 [marketplace 7/7] RUN python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=.     --grpc_python_out=. ../protos/recommendations.proto
#21 CACHED

#22 [recommendations] exporting to image
#22 exporting layers done
#22 writing image sha256:cafd7218293ee01e1419699cc61f440da0f82454038b7c5171ee3e677d754ba1 done
#22 naming to docker.io/library/recommendations 0.0s done
#22 DONE 0.0s

#23 [marketplace] exporting to image
#23 exporting layers done
#23 writing image sha256:242c38a94e4bc03c56dc3d781444ed85421ef2479959b2921ed9b57829e8c6b5 done
#23 naming to docker.io/library/marketplace done
#23 DONE 0.0s

#24 [recommendations] resolving provenance for metadata file
#24 DONE 0.0s

#25 [marketplace] resolving provenance for metadata file
#25 DONE 0.0s
 Image recommendations Building 
 Image marketplace Building 
 Image recommendations Built 
 Image marketplace Built 
 Network microservices_default Creating 
 Network microservices_default Creating 
 Network microservices_default Created 
 Network microservices_default Created 
 Container microservices-recommendations-1 Creating 
 Container microservices-recommendations-1 Created 
 Container microservices-marketplace-1 Creating 
 Container microservices-marketplace-1 Created 
 Container microservices-recommendations-1 Starting 
 Container microservices-recommendations-1 Started 
 Container microservices-marketplace-1 Starting 
 Container microservices-marketplace-1 Started 

[5.8 с]
```

Команда:

```shell
$ docker compose ps
```

Вывод:

```text
NAME                              IMAGE             COMMAND                  SERVICE           CREATED         STATUS         PORTS
microservices-marketplace-1       marketplace       "uvicorn marketplace…"   marketplace       4 seconds ago   Up 2 seconds   127.0.0.1:8888->8000/tcp
microservices-recommendations-1   recommendations   "python recommendati…"   recommendations   4 seconds ago   Up 3 seconds   50051/tcp

[0.3 с]
```

Команда:

```shell
$ GET http://127.0.0.1:8888/api/v1/recommendations?user_id=1
```

Вывод:

```text
HTTP 200
[
  {
    "id": 4,
    "title": "The Name of the Rose"
  },
  {
    "id": 1,
    "title": "The Maltese Falcon"
  },
  {
    "id": 2,
    "title": "Murder on the Orient Express"
  }
]
```

Команда:

```shell
$ docker compose exec -T recommendations pytest -q
```

Вывод:

```text
.....                                                                    [100%]
5 passed in 0.21s

[1.4 с]
```

Команда:

```shell
$ docker compose exec -T marketplace pytest -q test_marketplace_integration.py
```

Вывод:

```text
..                                                                       [100%]
2 passed in 0.08s

[1.6 с]
```

Команда:

```shell
$ docker compose logs --no-color --tail 15
```

Вывод:

```text
marketplace-1      | INFO:     Started server process [1]
recommendations-1  | Recommendations service listening on 50051
marketplace-1      | INFO:     Waiting for application startup.
marketplace-1      | INFO:     Application startup complete.
marketplace-1      | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
marketplace-1      | INFO:     172.21.0.1:56226 - "GET /openapi.json HTTP/1.1" 200 OK
marketplace-1      | INFO:     172.21.0.1:56236 - "GET /api/v1/recommendations?user_id=1 HTTP/1.1" 200 OK
marketplace-1      | INFO:     127.0.0.1:42172 - "GET / HTTP/1.1" 200 OK
marketplace-1      | INFO:     127.0.0.1:42186 - "GET /api/v1/recommendations?user_id=1&category=science_fiction&max_results=2 HTTP/1.1" 200 OK

[0.4 с]
```

Команда:

```shell
$ docker compose down
```

Вывод:

```text
 Container microservices-marketplace-1 Stopping 
 Container microservices-marketplace-1 Stopped 
 Container microservices-marketplace-1 Removing 
 Container microservices-marketplace-1 Removed 
 Container microservices-recommendations-1 Stopping 
 Container microservices-recommendations-1 Stopped 
 Container microservices-recommendations-1 Removing 
 Container microservices-recommendations-1 Removed 
 Network microservices_default Removing 
 Network microservices_default Removed 

[4.7 с]
```
