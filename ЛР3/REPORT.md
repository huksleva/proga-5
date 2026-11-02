# Отчёт по ЛР3: Protocol Buffers и gRPC, микросервисы Recommendations + Marketplace

Сформирован автоматически скриптом `run_lab.py`: 2026-11-02 13:54:47, Windows-10-10.0.19045-SP0, Python 3.13.2.

Все выводы ниже — реальные, получены при локальном запуске. Подробный порядок развёртывания — в [README.md](README.md).

## Итоги прогона

| Шаг | Результат |
|---|---|
| Версии окружения | OK |
| Генерация кода protoc | OK |
| Часть 1: protobuf без gRPC | ОШИБКА |
| Часть 2: байты и эволюция схемы | OK |
| Hello World: клиент | OK |
| Hello World: ошибка типа аргумента | OK |
| Потоковые вызовы gRPC | OK |
| Ошибки, дедлайны, метаданные, grpc.aio | OK |
| Микросервисы: запуск Marketplace | ОШИБКА |
| docker compose up --build -d | ОШИБКА |
| docker compose ps | OK |
| Docker: Marketplace → Recommendations | ОШИБКА |
| Docker: pytest в контейнере recommendations | OK |
| Docker: pytest в контейнере marketplace | ОШИБКА |
| docker compose logs | OK |
| docker compose down | OK |

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

[2.3 с]
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

[1.6 с]
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

Вывод (ОШИБКА):

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
Сериализация: protobuf 0.269 мс, json 2.415 мс
Разбор:       protobuf 0.569 мс, json 2.596 мс

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
Traceback (most recent call last):
  File "C:\Leo\projects\proga-5\ЛР3\part1_protobuf.py", line 92, in <module>
    b.published_at = Timestamp()
    ^^^^^^^^^^^^^^
  File "C:\Leo\projects\proga-5\ЛР3\.venv\Lib\site-packages\google\protobuf\internal\well_known_types.py", line 301, in _internal_assign
    self.FromDatetime(dt)
    ~~~~~~~~~~~~~~~~~^^^^
  File "C:\Leo\projects\proga-5\ЛР3\.venv\Lib\site-packages\google\protobuf\internal\well_known_types.py", line 284, in FromDatetime
    raise TypeError(
    ...<2 lines>...
    )
TypeError: Fail to convert to Timestamp. Expected a datetime object got Timestamp

[код завершения 1]
[1.5 с]
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

[0.6 с]
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

[2.2 с]
```


## 6. Часть 6. Микросервисы Recommendations и Marketplace (локально)

```
Браузер / curl --HTTP, REST, JSON--> Marketplace (FastAPI, :8000)
                                          | gRPC, Protobuf
                                          v
                                     Recommendations (:50051)
```

Контракт `microservices/protos/recommendations.proto` общий; код из него генерируется в каталог каждого сервиса (это уже сделано на шаге 1).

Команда:

```shell
$ python -m uvicorn marketplace:app --port 8000
```

Вывод (ОШИБКА):

```text
[Marketplace не запустился]
INFO:     Started server process [2828]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
ERROR:    [Errno 13] error while attempting to bind on address ('127.0.0.1', 8000): [winerror 10013] сделана попытка доступа к сокету методом, запрещенным правами доступа
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
```


## 7. Часть 6.4–6.5. Контейнеризация и Docker Compose

Каждый сервис — отдельный образ (`microservices/*/Dockerfile`), контекст сборки — каталог `microservices/`, код из `.proto` генерируется внутри образа. `compose.yaml` описывает обе службы; сеть создаётся автоматически, Marketplace обращается к Recommendations по имени службы (`RECOMMENDATIONS_HOST=recommendations`). Порт Recommendations наружу не публикуется.

Команда:

```shell
$ docker compose up --build -d
```

Вывод (ОШИБКА):

```text
#1 [internal] load local bake definitions
#1 reading from stdin 1.09kB 0.1s done
#1 DONE 0.1s

#2 [marketplace internal] load build definition from Dockerfile
#2 transferring dockerfile: 447B 0.0s done
#2 DONE 0.1s

#3 [recommendations internal] load build definition from Dockerfile
#3 transferring dockerfile: 423B done
#3 DONE 0.1s

#4 [recommendations internal] load metadata for docker.io/library/python:3.12-slim
#4 ...

#5 [auth] library/python:pull token for registry-1.docker.io
#5 DONE 0.0s

#4 [recommendations internal] load metadata for docker.io/library/python:3.12-slim
#4 DONE 6.1s

#6 [recommendations internal] load .dockerignore
#6 transferring context: 114B 0.0s done
#6 DONE 0.1s

#7 [recommendations 1/7] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#7 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#7 ...

#8 [marketplace internal] load build context
#8 transferring context: 5.26kB 0.0s done
#8 DONE 0.1s

#9 [recommendations internal] load build context
#9 transferring context: 5.69kB 0.0s done
#9 DONE 0.1s

#7 [recommendations 1/7] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#7 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 0.1s done
#7 sha256:ae4e8b7c575fabea88a029b6cae757f342ca2525e07f7c22272d5105c346b35e 5.66kB / 5.66kB done
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 0B / 29.86MB 0.1s
#7 sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 0B / 1.29MB 0.1s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 0B / 12.12MB 0.1s
#7 sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 10.37kB / 10.37kB done
#7 sha256:1148dbb014615300fa7e713b2f94f550c0d1c69780c0805f84f093ceee34dd0b 1.75kB / 1.75kB done
#7 sha256:ae4e8b7c575fabea88a029b6cae757f342ca2525e07f7c22272d5105c346b35e 5.66kB / 5.66kB done
#7 sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 10.37kB / 10.37kB done
#7 sha256:1148dbb014615300fa7e713b2f94f550c0d1c69780c0805f84f093ceee34dd0b 1.75kB / 1.75kB done
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 1.05MB / 12.12MB 1.6s
#7 sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 1.05MB / 1.29MB 2.3s
#7 sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 1.29MB / 1.29MB 2.4s done
#7 sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e 0B / 251B 2.5s
#7 sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 1.29MB / 1.29MB 2.4s done
#7 sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e 251B / 251B 2.8s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 2.10MB / 12.12MB 3.0s
#7 sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e 251B / 251B 2.8s done
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 2.10MB / 29.86MB 3.6s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 3.15MB / 12.12MB 4.0s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 4.19MB / 12.12MB 5.2s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 4.19MB / 29.86MB 5.6s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 5.24MB / 12.12MB 6.3s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 6.29MB / 12.12MB 7.2s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 6.29MB / 29.86MB 8.0s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 7.34MB / 12.12MB 8.4s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 8.39MB / 12.12MB 9.4s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 8.39MB / 29.86MB 10.4s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 9.44MB / 12.12MB 10.8s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 10.49MB / 12.12MB 11.7s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 10.49MB / 29.86MB 12.7s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 11.53MB / 12.12MB 12.8s
#7 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 12.12MB / 12.12MB 13.4s done
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 12.58MB / 29.86MB 14.9s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 14.68MB / 29.86MB 17.1s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 16.78MB / 29.86MB 19.5s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 18.87MB / 29.86MB 22.3s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 20.97MB / 29.86MB 24.8s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 23.07MB / 29.86MB 27.0s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 25.17MB / 29.86MB 28.9s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 27.26MB / 29.86MB 31.3s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 29.36MB / 29.86MB 33.2s
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 29.86MB / 29.86MB 33.7s done
#7 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 29.86MB / 29.86MB 33.7s done
#7 extracting sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5
#7 extracting sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 3.8s done
#7 extracting sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35
#7 extracting sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 0.6s done
#7 extracting sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3
#7 extracting sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 2.5s done
#7 extracting sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e
#7 extracting sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e done
#7 DONE 41.4s

#10 [recommendations 2/7] WORKDIR /service/recommendations
#10 ...

#11 [marketplace 2/7] WORKDIR /service/marketplace
#11 DONE 0.5s

#10 [recommendations 2/7] WORKDIR /service/recommendations
#10 DONE 0.5s

#12 [marketplace 3/7] COPY marketplace/requirements.txt .
#12 DONE 0.1s

#13 [recommendations 3/7] COPY recommendations/requirements.txt .
#13 DONE 0.1s

#14 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#14 4.720 Collecting fastapi (from -r requirements.txt (line 1))
#14 5.235   Downloading fastapi-0.162.0-py3-none-any.whl.metadata (26 kB)
#14 7.185 Collecting grpcio (from -r requirements.txt (line 3))
#14 7.292   Downloading grpcio-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.8 kB)
#14 9.944 Collecting grpcio-tools (from -r requirements.txt (line 4))
#14 10.04   Downloading grpcio_tools-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (5.3 kB)
#14 ...

#15 [recommendations 4/7] RUN pip install --no-cache-dir -r requirements.txt
#15 6.662 Collecting grpcio (from -r requirements.txt (line 1))
#15 7.402   Downloading grpcio-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.8 kB)
#15 10.06 Collecting grpcio-tools (from -r requirements.txt (line 2))
#15 10.17   Downloading grpcio_tools-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (5.3 kB)
#15 ...

#14 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#14 10.30 Collecting pytest (from -r requirements.txt (line 5))
#14 10.39   Downloading pytest-9.2.0-py3-none-any.whl.metadata (7.9 kB)
#14 10.56 Collecting uvicorn[standard] (from -r requirements.txt (line 2))
#14 10.66   Downloading uvicorn-0.54.0-py3-none-any.whl.metadata (6.6 kB)
#14 10.83 Collecting starlette>=0.46.0 (from fastapi->-r requirements.txt (line 1))
#14 10.93   Downloading starlette-1.10.0-py3-none-any.whl.metadata (6.6 kB)
#14 11.44 Collecting pydantic>=2.9.0 (from fastapi->-r requirements.txt (line 1))
#14 11.53   Downloading pydantic-2.14.2-py3-none-any.whl.metadata (137 kB)
#14 11.91 Collecting typing-extensions>=4.8.0 (from fastapi->-r requirements.txt (line 1))
#14 12.00   Downloading typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
#14 12.16 Collecting typing-inspection>=0.4.2 (from fastapi->-r requirements.txt (line 1))
#14 12.26   Downloading typing_inspection-0.4.4-py3-none-any.whl.metadata (2.6 kB)
#14 12.35 Collecting annotated-doc>=0.0.2 (from fastapi->-r requirements.txt (line 1))
#14 12.46   Downloading annotated_doc-0.0.5-py3-none-any.whl.metadata (6.5 kB)
#14 12.60 Collecting opentelemetry-api>=1.44.0 (from fastapi->-r requirements.txt (line 1))
#14 12.69   Downloading opentelemetry_api-1.45.2-py3-none-any.whl.metadata (1.4 kB)
#14 12.86 Collecting click>=7.0 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 12.99   Downloading click-8.5.0-py3-none-any.whl.metadata (2.6 kB)
#14 13.14 Collecting h11>=0.8 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 13.24   Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
#14 13.80 Collecting httptools>=0.8.0 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 13.92   Downloading httptools-0.9.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
#14 14.12 Collecting python-dotenv>=0.13 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 14.21   Downloading python_dotenv-1.2.4-py3-none-any.whl.metadata (29 kB)
#14 14.56 Collecting pyyaml>=5.1 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 14.65   Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.4 kB)
#14 14.88 Collecting uvloop>=0.15.1 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 14.99   Downloading uvloop-0.23.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (5.1 kB)
#14 15.30 Collecting watchfiles>=0.20 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 15.40   Downloading watchfiles-1.3.0-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
#14 16.18 Collecting websockets>=13.0 (from uvicorn[standard]->-r requirements.txt (line 2))
#14 16.30   Downloading websockets-17.4-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (6.3 kB)
#14 16.92 Collecting protobuf<8.0.0,>=7.35.1 (from grpcio-tools->-r requirements.txt (line 4))
#14 17.03   Downloading protobuf-7.36.2-cp310-abi3-manylinux2014_x86_64.whl.metadata (595 bytes)
#14 17.47 Collecting setuptools>=77.0.1 (from grpcio-tools->-r requirements.txt (line 4))
#14 17.56   Downloading setuptools-84.2.1-py3-none-any.whl.metadata (6.6 kB)
#14 17.74 Collecting iniconfig>=2 (from pytest->-r requirements.txt (line 5))
#14 17.83   Downloading iniconfig-2.3.1-py3-none-any.whl.metadata (2.8 kB)
#14 18.00 Collecting packaging>=24 (from pytest->-r requirements.txt (line 5))
#14 18.12   Downloading packaging-26.3-py3-none-any.whl.metadata (3.5 kB)
#14 18.29 Collecting pluggy<2,>=1.6 (from pytest->-r requirements.txt (line 5))
#14 18.40   Downloading pluggy-1.7.0-py3-none-any.whl.metadata (5.0 kB)
#14 18.65 Collecting pygments>=2.15 (from pytest->-r requirements.txt (line 5))
#14 18.76   Downloading pygments-2.21.0-py3-none-any.whl.metadata (2.5 kB)
#14 18.92 Collecting annotated-types>=0.6.0 (from pydantic>=2.9.0->fastapi->-r requirements.txt (line 1))
#14 19.04   Downloading annotated_types-0.8.0-py3-none-any.whl.metadata (15 kB)
#14 ...

#15 [recommendations 4/7] RUN pip install --no-cache-dir -r requirements.txt
#15 10.41 Collecting pytest (from -r requirements.txt (line 3))
#15 10.52   Downloading pytest-9.2.0-py3-none-any.whl.metadata (7.9 kB)
#15 10.69 Collecting typing-extensions~=4.12 (from grpcio->-r requirements.txt (line 1))
#15 10.79   Downloading typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
#15 11.55 Collecting protobuf<8.0.0,>=7.35.1 (from grpcio-tools->-r requirements.txt (line 2))
#15 11.68   Downloading protobuf-7.36.2-cp310-abi3-manylinux2014_x86_64.whl.metadata (595 bytes)
#15 12.21 Collecting setuptools>=77.0.1 (from grpcio-tools->-r requirements.txt (line 2))
#15 12.31   Downloading setuptools-84.2.1-py3-none-any.whl.metadata (6.6 kB)
#15 12.42 Collecting iniconfig>=2 (from pytest->-r requirements.txt (line 3))
#15 12.50   Downloading iniconfig-2.3.1-py3-none-any.whl.metadata (2.8 kB)
#15 12.62 Collecting packaging>=24 (from pytest->-r requirements.txt (line 3))
#15 12.71   Downloading packaging-26.3-py3-none-any.whl.metadata (3.5 kB)
#15 12.83 Collecting pluggy<2,>=1.6 (from pytest->-r requirements.txt (line 3))
#15 12.93   Downloading pluggy-1.7.0-py3-none-any.whl.metadata (5.0 kB)
#15 13.06 Collecting pygments>=2.15 (from pytest->-r requirements.txt (line 3))
#15 13.30   Downloading pygments-2.21.0-py3-none-any.whl.metadata (2.5 kB)
#15 13.43 Downloading grpcio-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (7.4 MB)
#15 ...

#14 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#14 22.03 Collecting pydantic-core==2.50.2 (from pydantic>=2.9.0->fastapi->-r requirements.txt (line 1))
#14 22.12   Downloading pydantic_core-2.50.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (6.5 kB)
#14 22.42 Collecting anyio<5,>=4.0.0 (from starlette>=0.46.0->fastapi->-r requirements.txt (line 1))
#14 22.52   Downloading anyio-4.16.0-py3-none-any.whl.metadata (4.7 kB)
#14 22.92 Collecting idna>=2.8 (from anyio<5,>=4.0.0->starlette>=0.46.0->fastapi->-r requirements.txt (line 1))
#14 23.08   Downloading idna-3.20-py3-none-any.whl.metadata (7.2 kB)
#14 23.48 Downloading fastapi-0.162.0-py3-none-any.whl (148 kB)
#14 24.17 Downloading grpcio-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (7.4 MB)
#14 ...

#15 [recommendations 4/7] RUN pip install --no-cache-dir -r requirements.txt
#15 22.16    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7.4/7.4 MB 909.6 kB/s eta 0:00:00
#15 22.31 Downloading grpcio_tools-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (2.8 MB)
#15 26.15    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.8/2.8 MB 707.2 kB/s eta 0:00:00
#15 28.37 Downloading pytest-9.2.0-py3-none-any.whl (411 kB)
#15 28.62 Downloading iniconfig-2.3.1-py3-none-any.whl (7.6 kB)
#15 28.72 Downloading packaging-26.3-py3-none-any.whl (129 kB)
#15 29.03 Downloading pluggy-1.7.0-py3-none-any.whl (27 kB)
#15 29.32 Downloading protobuf-7.36.2-cp310-abi3-manylinux2014_x86_64.whl (343 kB)
#15 30.06 Downloading pygments-2.21.0-py3-none-any.whl (1.3 MB)
#15 32.58    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 488.8 kB/s eta 0:00:00
#15 32.70 Downloading setuptools-84.2.1-py3-none-any.whl (876 kB)
#15 33.35    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 876.3/876.3 kB 1.4 MB/s eta 0:00:00
#15 33.49 Downloading typing_extensions-4.16.0-py3-none-any.whl (45 kB)
#15 33.64 Installing collected packages: typing-extensions, setuptools, pygments, protobuf, pluggy, packaging, iniconfig, pytest, grpcio, grpcio-tools
#15 ...

#14 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#14 36.79    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7.4/7.4 MB 621.2 kB/s eta 0:00:00
#14 36.94 Downloading grpcio_tools-1.85.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (2.8 MB)
#14 39.66    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.8/2.8 MB 977.8 kB/s eta 0:00:00
#14 39.75 Downloading pytest-9.2.0-py3-none-any.whl (411 kB)
#14 40.34 Downloading annotated_doc-0.0.5-py3-none-any.whl (5.3 kB)
#14 40.43 Downloading click-8.5.0-py3-none-any.whl (125 kB)
#14 40.67 Downloading h11-0.16.0-py3-none-any.whl (37 kB)
#14 40.79 Downloading httptools-0.9.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (552 kB)
#14 41.05    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 552.8/552.8 kB 2.1 MB/s eta 0:00:00
#14 41.14 Downloading iniconfig-2.3.1-py3-none-any.whl (7.6 kB)
#14 41.24 Downloading opentelemetry_api-1.45.2-py3-none-any.whl (60 kB)
#14 ...

#15 [recommendations 4/7] RUN pip install --no-cache-dir -r requirements.txt
#15 38.55 Successfully installed grpcio-1.85.1 grpcio-tools-1.85.1 iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 protobuf-7.36.2 pygments-2.21.0 pytest-9.2.0 setuptools-84.2.1 typing-extensions-4.16.0
#15 38.55 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.
#15 40.70 
#15 40.70 [notice] A new release of pip is available: 25.0.1 -> 26.2.2
#15 40.70 [notice] To update, run: pip install --upgrade pip
#15 DONE 41.3s

#16 [recommendations 5/7] COPY protos/ /service/protos/
#16 DONE 0.1s

#17 [recommendations 6/7] COPY recommendations/ .
#17 DONE 0.1s

#14 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#14 41.41 Downloading packaging-26.3-py3-none-any.whl (129 kB)
#14 41.63 Downloading pluggy-1.7.0-py3-none-any.whl (27 kB)
#14 41.74 Downloading protobuf-7.36.2-cp310-abi3-manylinux2014_x86_64.whl (343 kB)
#14 ...

#18 [recommendations 7/7] RUN python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=.     --grpc_python_out=. ../protos/recommendations.proto
#18 DONE 0.5s

#19 [recommendations] exporting to image
#19 exporting layers
#19 exporting layers 1.0s done
#19 writing image sha256:cafd7218293ee01e1419699cc61f440da0f82454038b7c5171ee3e677d754ba1 done
#19 naming to docker.io/library/recommendations 0.0s done
#19 DONE 1.0s

#20 [recommendations] resolving provenance for metadata file
#20 DONE 0.0s

#14 [marketplace 4/7] RUN pip install --no-cache-dir -r requirements.txt
#14 42.15 Downloading pydantic-2.14.2-py3-none-any.whl (490 kB)
#14 42.60 Downloading pydantic_core-2.50.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (2.2 MB)
#14 43.87    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 2.0 MB/s eta 0:00:00
#14 43.96 Downloading pygments-2.21.0-py3-none-any.whl (1.3 MB)
#14 45.06    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 1.1 MB/s eta 0:00:00
#14 45.15 Downloading python_dotenv-1.2.4-py3-none-any.whl (23 kB)
#14 45.27 Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
#14 45.98    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 807.9/807.9 kB 1.2 MB/s eta 0:00:00
#14 46.08 Downloading setuptools-84.2.1-py3-none-any.whl (876 kB)
#14 46.66    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 876.3/876.3 kB 2.1 MB/s eta 0:00:00
#14 46.75 Downloading starlette-1.10.0-py3-none-any.whl (80 kB)
#14 46.92 Downloading typing_extensions-4.16.0-py3-none-any.whl (45 kB)
#14 47.05 Downloading typing_inspection-0.4.4-py3-none-any.whl (14 kB)
#14 47.12 Downloading uvloop-0.23.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.5 MB)
#14 49.92    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.5/4.5 MB 1.8 MB/s eta 0:00:00
#14 50.00 Downloading watchfiles-1.3.0-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (458 kB)
#14 50.30 Downloading websockets-17.4-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (226 kB)
#14 50.48 Downloading uvicorn-0.54.0-py3-none-any.whl (87 kB)
#14 50.62 Downloading annotated_types-0.8.0-py3-none-any.whl (13 kB)
#14 50.73 Downloading anyio-4.16.0-py3-none-any.whl (134 kB)
#14 50.94 Downloading idna-3.20-py3-none-any.whl (69 kB)
#14 51.19 Installing collected packages: websockets, uvloop, typing-extensions, setuptools, pyyaml, python-dotenv, pygments, protobuf, pluggy, packaging, iniconfig, idna, httptools, h11, click, annotated-types, annotated-doc, uvicorn, typing-inspection, pytest, pydantic-core, opentelemetry-api, grpcio, anyio, watchfiles, starlette, pydantic, grpcio-tools, fastapi
#14 58.28 Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.16.0 click-8.5.0 fastapi-0.162.0 grpcio-1.85.1 grpcio-tools-1.85.1 h11-0.16.0 httptools-0.9.0 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.2 packaging-26.3 pluggy-1.7.0 protobuf-7.36.2 pydantic-2.14.2 pydantic-core-2.50.2 pygments-2.21.0 pytest-9.2.0 python-dotenv-1.2.4 pyyaml-6.0.3 setuptools-84.2.1 starlette-1.10.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0 uvloop-0.23.0 watchfiles-1.3.0 websockets-17.4
#14 58.28 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.
#14 58.98 
#14 58.98 [notice] A new release of pip is available: 25.0.1 -> 26.2.2
#14 58.98 [notice] To update, run: pip install --upgrade pip
#14 DONE 59.6s

#21 [marketplace 5/7] COPY protos/ /service/protos/
#21 DONE 0.1s

#22 [marketplace 6/7] COPY marketplace/ .
#22 DONE 0.1s

#23 [marketplace 7/7] RUN python -m grpc_tools.protoc -I ../protos --python_out=. --pyi_out=.     --grpc_python_out=. ../protos/recommendations.proto
#23 DONE 0.5s

#24 [marketplace] exporting to image
#24 exporting layers
#24 exporting layers 1.4s done
#24 writing image sha256:242c38a94e4bc03c56dc3d781444ed85421ef2479959b2921ed9b57829e8c6b5 done
#24 naming to docker.io/library/marketplace 0.0s done
#24 DONE 1.4s

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
Error response from daemon: ports are not available: exposing port TCP 127.0.0.1:8000 -> 127.0.0.1:0: listen tcp4 127.0.0.1:8000: bind: An attempt was made to access a socket in a way forbidden by its access permissions.

[код завершения 1]
[119.4 с]
```

Команда:

```shell
$ docker compose ps
```

Вывод:

```text
NAME                              IMAGE             COMMAND                  SERVICE           CREATED              STATUS              PORTS
microservices-recommendations-1   recommendations   "python recommendati…"   recommendations   About a minute ago   Up About a minute   50051/tcp

[0.4 с]
```

Команда:

```shell
$ GET http://127.0.0.1:8000/api/v1/recommendations?user_id=1
```

Вывод (ОШИБКА):

```text
[ошибка соединения: <urlopen error [WinError 10061] Подключение не установлено, т.к. конечный компьютер отверг запрос на подключение>]
```

Команда:

```shell
$ docker compose exec -T recommendations pytest -q
```

Вывод:

```text
.....                                                                    [100%]
5 passed in 0.23s

[1.4 с]
```

Команда:

```shell
$ docker compose exec -T marketplace pytest -q test_marketplace_integration.py
```

Вывод (ОШИБКА):

```text
service "marketplace" is not running

[код завершения 1]
[0.3 с]
```

Команда:

```shell
$ docker compose logs --no-color --tail 15
```

Вывод:

```text
recommendations-1  | Recommendations service listening on 50051

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

[4.0 с]
```
