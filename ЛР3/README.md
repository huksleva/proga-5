# ЛР3. Protocol Buffers и gRPC: микросервисы Recommendations + Marketplace

Лабораторная работа по практике к лекции 2 «Микросервисы. Проектирование веб-сервисов» (дисциплина «Программирование на Python»).
Ноутбук-образец (Colab «Protobuf_gRPC_практика») перенесён в обычный локальный проект: ячейки `%%writefile` превращены в файлы репозитория, ячейки `!protoc` — в скрипт `generate.py`, а `%pip install` — в зависимости `pyproject.toml`.

**Отчёт о развёртывании и работе сервисов — [REPORT.md](REPORT.md)** (формируется скриптом `run_lab.py`, все выводы в нём реальные).

## Что реализовано

| Часть ноутбука | Файлы |
|---|---|
| 0. Окружение | `pyproject.toml`, `env_info.py` |
| 1. Protocol Buffers без gRPC | `protos/library/v1/library.proto`, `part1_protobuf.py` |
| 2. Байты, varint/zigzag, эволюция схемы | `protos/encoding_demo.proto`, `protos/evolution/v{1,2}/user.proto`, `part2_bytes.py` |
| 3. gRPC Hello World (+ `SayMyName`, ошибка типа аргумента) | `protos/helloworld.proto`, `greeter_server.py`, `greeter_client.py`, `wrong_type_client.py` |
| 4. Потоковые вызовы (3 вида) | `protos/stats.proto`, `stats_server.py`, `stats_demo.py` |
| 5. Ошибки, дедлайны, метаданные, `grpc.aio`, reflection | `protos/library/v1/library_service.proto`, `library_server.py`, `library_demo.py` |
| 6. Микросервисы + тесты | `microservices/recommendations/`, `microservices/marketplace/`, `microservices/protos/recommendations.proto` |
| 6.4–6.5. Docker и Docker Compose | `microservices/*/Dockerfile`, `microservices/compose.yaml`, `microservices/.dockerignore` |

Дополнительно из упражнений для самопроверки: метод `SayGoodbye` в `Greeter` (упр. 1) и размер сообщения `Demo(a=300)` (упр. 2).

Архитектура части 6 (снаружи REST, внутри gRPC):

```
Браузер / curl --HTTP, REST, JSON--> Marketplace (FastAPI, :8000)
                                          | gRPC, Protobuf
                                          v
                                     Recommendations (:50051)
```

## Требования

- Python 3.10+
- Docker с Docker Compose v2 (только для части 6.4–6.5; без него остальное работает)

## Развёртывание

Все команды — из каталога `ЛР3`.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Зависимости описаны в `pyproject.toml`; `pip install .` ставит только их (проект — набор скриптов, а не пакет). У микросервисов остаются свои `requirements.txt` — их используют Dockerfile-ы при сборке образов.

### Быстрый путь: одна команда

```bash
python run_lab.py              # все шаги + Docker Compose, если Docker запущен
python run_lab.py --no-docker  # без Docker
```

Скрипт генерирует код из `.proto`, по очереди выполняет все части практики, поднимает и останавливает серверы, запускает тесты и записывает **REPORT.md** с реальными выводами.

### Пошагово, вручную

```bash
# 1. сгенерировать *_pb2.py / *_pb2_grpc.py из .proto
python generate.py

# 2. части 1-2: protobuf и байты
python part1_protobuf.py
python part2_bytes.py

# 3. Hello World: два терминала
python greeter_server.py          # терминал 1
python greeter_client.py          # терминал 2
python wrong_type_client.py       # демонстрация ошибки типа аргумента

# 4-5. потоки; ошибки, дедлайны, метаданные
python stats_demo.py
python library_demo.py
```

Сгенерированный код в репозиторий не коммитится (`.gitignore`), его создаёт `generate.py`. После любого изменения `.proto` код нужно сгенерировать заново.

### Микросервисы локально (без Docker)

```bash
# терминал 1
cd microservices/recommendations
python recommendations.py

# терминал 2
cd microservices/marketplace
python -m uvicorn marketplace:app --port 8000     # (Windows PowerShell: $env:RECOMMENDATIONS_HOST="localhost")
```

Проверка:

- http://127.0.0.1:8000/ — HTML-страница с тремя книгами;
- http://127.0.0.1:8000/docs — документация OpenAPI (Swagger UI);
- `curl "http://127.0.0.1:8000/api/v1/recommendations?user_id=1&category=science_fiction&max_results=2"`.

Тесты:

```bash
cd microservices/recommendations && python -m pytest -q
cd microservices/marketplace && python -m pytest -q test_marketplace_integration.py   # сервисы должны быть запущены
```

### Docker Compose

```bash
cd microservices
docker compose up --build -d          # собрать образы и запустить в фоне
docker compose ps                     # состояние служб
curl "http://127.0.0.1:8000/api/v1/recommendations?user_id=1"
docker compose exec recommendations pytest -q
docker compose exec marketplace pytest -q test_marketplace_integration.py
docker compose logs -f marketplace
docker compose down                   # остановить и удалить контейнеры и сеть
```

Контекст сборки — `microservices/`, поэтому в образ попадает общий каталог `protos/`; код из `.proto` генерируется при сборке образа. Marketplace находит Recommendations по имени службы (`RECOMMENDATIONS_HOST=recommendations`); порт Recommendations наружу не публикуется.

### Типичные проблемы

- `ModuleNotFoundError: library...` / `*_pb2` — не выполнен `python generate.py` или скрипт запущен не из каталога `ЛР3`.
- Порт 50051 / 8000 занят — остановите предыдущий запуск (в `run_lab.py` серверы поднимаются по очереди и гасятся сами).
- Marketplace отвечает 503 — Recommendations не запущен или недоступен по адресу `RECOMMENDATIONS_HOST:RECOMMENDATIONS_PORT`.
