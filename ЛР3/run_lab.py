#!/usr/bin/env python3
"""Прогон всей ЛР3 одной командой и сборка отчёта REPORT.md с реальными выводами.

Что делает скрипт (повторяет шаги ноутбука «Protobuf_gRPC_практика» локально):
  0. печатает версии окружения;
  1. генерирует код из всех .proto (generate.py);
  2. часть 1-2: protobuf без gRPC, байты, эволюция схемы;
  3. часть 3: gRPC Hello World (сервер + клиент + ошибка типа аргумента);
  4. часть 4: потоковые вызовы;
  5. часть 5: метаданные, коды статуса, дедлайны, grpc.aio, reflection;
  6. часть 6: микросервисы Recommendations + Marketplace локально, тесты, отказ сервиса;
  7. часть 6.4-6.5: Docker Compose (если Docker доступен; отключается --no-docker).

Запуск (из каталога ЛР3, в активированном виртуальном окружении):
    python run_lab.py
    python run_lab.py --no-docker
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MS = ROOT / "microservices"
LOGS = ROOT / ".logs"
PY = sys.executable
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}

report: list[str] = []
summary: list[tuple[str, bool]] = []


# ---------------------------------------------------------------- вспомогательные функции
def shown(cmd: list[str]) -> str:
    """Команда в «портативном» виде для отчёта."""
    parts = ["python" if part == PY else part for part in cmd]
    return " ".join(parts)


def fence(text: str, lang: str = "text") -> str:
    return f"```{lang}\n{text.rstrip()}\n```\n"


def heading(text: str) -> None:
    print(f"\n##### {text}", flush=True)
    report.append(f"\n## {text}\n")


def prose(text: str) -> None:
    report.append(text.strip() + "\n")


def record(command: str, output: str, ok: bool = True, title: str | None = None) -> None:
    report.append(f"Команда:\n\n{fence('$ ' + command, 'shell')}")
    report.append(f"Вывод{'' if ok else ' (ОШИБКА)'}:\n\n{fence(output)}")
    if title is not None:
        summary.append((title, ok))
    print(output, flush=True)


def run(cmd: list[str], cwd: Path = ROOT, title: str | None = None, timeout: int = 180,
        env: dict | None = None, display: str | None = None) -> tuple[bool, str]:
    """Запускает команду, пишет её и вывод в отчёт."""
    started = time.monotonic()
    try:
        done = subprocess.run(cmd, cwd=cwd, env=env or ENV, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        output = (done.stdout or "") + (done.stderr or "")
        ok = done.returncode == 0
        if not ok:
            output += f"\n[код завершения {done.returncode}]"
    except subprocess.TimeoutExpired as error:
        output = f"[превышено время ожидания {timeout} с]\n{error.stdout or ''}"
        ok = False
    except FileNotFoundError as error:
        output = f"[команда не найдена: {error}]"
        ok = False
    output += f"\n[{time.monotonic() - started:.1f} с]"
    record(display or shown(cmd), output, ok, title)
    return ok, output


class Background:
    """Фоновый процесс (сервер); вывод пишется в файл журнала."""

    def __init__(self, name: str, cmd: list[str], cwd: Path, env: dict | None = None) -> None:
        LOGS.mkdir(exist_ok=True)
        self.name = name
        self.cmd = cmd
        self.log_path = LOGS / f"{name}.log"
        self.log = open(self.log_path, "w", encoding="utf-8")
        self.process = subprocess.Popen(cmd, cwd=cwd, env=env or ENV, stdout=self.log,
                                        stderr=subprocess.STDOUT)

    def stop(self) -> str:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.log.close()
        return self.log_path.read_text(encoding="utf-8", errors="replace").strip()


def wait_port(port: int, timeout: float = 20) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def http_get(url: str, timeout: float = 10) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")


def http_step(url: str, title: str | None = None, expect: int = 200, pretty: bool = True) -> str:
    try:
        status, body = http_get(url)
    except Exception as error:  # сервис недоступен
        record(f"GET {url}", f"[ошибка соединения: {error}]", False, title)
        return ""
    if pretty:
        try:
            body = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
        except ValueError:
            pass
    record(f"GET {url}", f"HTTP {status}\n{body}", status == expect, title)
    return body


# ---------------------------------------------------------------- шаги
def step_env() -> None:
    heading("0. Окружение")
    prose("Работа выполняется локально в виртуальном окружении (`python -m venv .venv`), "
          "зависимости — из `pyproject.toml` (раздел «Подготовка окружения» ноутбука, "
          "`%pip install` заменён на `pip install .`).")
    run([PY, "env_info.py"], title="Версии окружения")


def step_generate() -> bool:
    heading("1. Генерация кода из .proto")
    prose("Компилятор `protoc` запускается как модуль `grpc_tools.protoc` (пакет `grpcio-tools`). "
          "Ключ `-I protos` задаёт корень поиска, поэтому путь Python-модуля повторяет путь "
          "`.proto`-файла (`library.v1.library_pb2`), а не директиву `package`.")
    ok, _ = run([PY, "generate.py"], title="Генерация кода protoc")
    if ok:
        files = sorted(str(p.relative_to(ROOT)).replace("\\", "/")
                       for p in ROOT.rglob("*_pb2*.py") if ".venv" not in p.parts)
        record("ls *_pb2*.py  # сгенерированные файлы", "\n".join(files))
    return ok


def step_part1_2() -> None:
    heading("2. Часть 1–2. Protocol Buffers без gRPC и устройство байтов")
    prose("Сообщения, сериализация, сравнение с JSON, значения по умолчанию, `oneof` (часть 1); "
          "ручной разбор wire format, varint/zigzag и эволюция схемы (часть 2). "
          "Последняя строка варианта «a = 300» — упражнение 2 для самопроверки.")
    run([PY, "part1_protobuf.py"], title="Часть 1: protobuf без gRPC")
    run([PY, "part2_bytes.py"], title="Часть 2: байты и эволюция схемы")


def step_hello() -> None:
    heading("3. Часть 3. Первый gRPC-сервис: Hello World")
    prose("Контракт `protos/helloworld.proto` содержит `SayHello`, `SayHelloAgain`, `SayMyName` "
          "(п. 3.4) и `SayGoodbye` (упражнение 1). Сервер запускается отдельным процессом, "
          "затем вызывается клиент.")
    server = Background("greeter_server", [PY, "greeter_server.py"], ROOT)
    if not wait_port(50051):
        record(shown(server.cmd), "[сервер не запустился]\n" + server.stop(), False, "Hello World: запуск сервера")
        return
    print("Сервер запущен", flush=True)
    run([PY, "greeter_client.py"], title="Hello World: клиент")
    prose("**Ошибка типа аргумента.** В `SayMyName` передано сообщение *ответа* вместо *запроса*. "
          "Вызов «случайно» работает: в двоичном сообщении нет имени типа, а у обоих сообщений "
          "поле 1 — строка.")
    run([PY, "wrong_type_client.py"], title="Hello World: ошибка типа аргумента")
    log = server.stop()
    record("# вывод сервера greeter_server.py", log or "(пусто)")


def step_stats() -> None:
    heading("4. Часть 4. Потоковые вызовы")
    prose("Серверный поток (`Countdown`), клиентский (`Sum`) и двунаправленный (`RunningAverage`), "
          "отмена потока клиентом и `INVALID_ARGUMENT`.")
    run([PY, "stats_demo.py"], title="Потоковые вызовы gRPC")


def step_library() -> None:
    heading("5. Часть 5. Ошибки, дедлайны, метаданные, grpc.aio")
    prose("`LibraryService`: метаданные запроса и ответа, коды статуса (`NOT_FOUND`, "
          "`INVALID_ARGUMENT`, `UNAUTHENTICATED`, `DEADLINE_EXCEEDED`), асинхронный клиент "
          "`grpc.aio` и server reflection (то, что делает `grpcurl list`).")
    run([PY, "library_demo.py"], title="Ошибки, дедлайны, метаданные, grpc.aio")


def step_microservices() -> None:
    heading("6. Часть 6. Микросервисы Recommendations и Marketplace (локально)")
    prose("```\nБраузер / curl --HTTP, REST, JSON--> Marketplace (FastAPI, :8000)\n"
          "                                          | gRPC, Protobuf\n"
          "                                          v\n"
          "                                     Recommendations (:50051)\n```")
    prose("Контракт `microservices/protos/recommendations.proto` общий; код из него генерируется "
          "в каталог каждого сервиса (это уже сделано на шаге 1).")

    rec = Background("recommendations", [PY, "recommendations.py"], MS / "recommendations")
    if not wait_port(50051):
        record("python recommendations.py", "[Recommendations не запустился]\n" + rec.stop(), False,
               "Микросервисы: запуск Recommendations")
        return
    mkt_env = {**ENV, "RECOMMENDATIONS_HOST": "localhost"}
    mkt = Background("marketplace", [PY, "-m", "uvicorn", "marketplace:app", "--port", "8000"],
                     MS / "marketplace", env=mkt_env)
    if not wait_port(8000):
        record("python -m uvicorn marketplace:app --port 8000",
               "[Marketplace не запустился]\n" + mkt.stop(), False, "Микросервисы: запуск Marketplace")
        rec.stop()
        return
    time.sleep(0.5)
    summary.append(("Микросервисы: оба сервиса запущены локально", True))
    prose("Оба сервиса запущены отдельными процессами. Документация OpenAPI: "
          "http://127.0.0.1:8000/docs.")

    http_step("http://127.0.0.1:8000/api/v1/recommendations?user_id=1&category=science_fiction&max_results=2",
              "Marketplace: REST API → gRPC")
    prose("Валидация FastAPI: `max_results=50` вне диапазона 1..10 → 422.")
    http_step("http://127.0.0.1:8000/api/v1/recommendations?user_id=1&max_results=50",
              "Marketplace: валидация (422)", expect=422)
    http_step("http://127.0.0.1:8000/", "Marketplace: HTML-страница", pretty=False)
    try:
        spec = json.loads(http_get("http://127.0.0.1:8000/openapi.json")[1])
        record("GET http://127.0.0.1:8000/openapi.json  # пути OpenAPI",
               "\n".join(f"{method.upper()} {path}" for path, item in spec["paths"].items() for method in item))
    except Exception as error:
        record("GET /openapi.json", f"[ошибка: {error}]", False)

    prose("Модульные тесты Recommendations и интеграционные тесты Marketplace:")
    run([PY, "-m", "pytest", "-q"], cwd=MS / "recommendations", title="pytest: Recommendations")
    run([PY, "-m", "pytest", "-q", "test_marketplace_integration.py"], cwd=MS / "marketplace",
        title="pytest: Marketplace (интеграционные)")

    prose("**Отказ зависимости.** Останавливаем Recommendations: Marketplace не падает, а возвращает 503.")
    rec_log = rec.stop()
    time.sleep(0.5)
    http_step("http://127.0.0.1:8000/api/v1/recommendations?user_id=1",
              "Marketplace: 503 при недоступном Recommendations", expect=503)
    mkt_log = mkt.stop()
    record("# вывод Recommendations", rec_log or "(пусто)")
    record("# вывод Marketplace (uvicorn)", mkt_log or "(пусто)")


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except Exception:
        return False


def step_docker() -> None:
    heading("7. Часть 6.4–6.5. Контейнеризация и Docker Compose")
    prose("Каждый сервис — отдельный образ (`microservices/*/Dockerfile`), контекст сборки — каталог "
          "`microservices/`, код из `.proto` генерируется внутри образа. `compose.yaml` описывает "
          "обе службы; сеть создаётся автоматически, Marketplace обращается к Recommendations по "
          "имени службы (`RECOMMENDATIONS_HOST=recommendations`). Порт Recommendations наружу не публикуется.")
    run(["docker", "compose", "up", "--build", "-d"], cwd=MS, timeout=900, title="docker compose up --build -d")
    ready = False
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and not ready:
        try:
            ready = http_get("http://127.0.0.1:8000/openapi.json", timeout=3)[0] == 200
        except Exception:
            time.sleep(1)
    run(["docker", "compose", "ps"], cwd=MS, title="docker compose ps")
    http_step("http://127.0.0.1:8000/api/v1/recommendations?user_id=1", "Docker: Marketplace → Recommendations")
    run(["docker", "compose", "exec", "-T", "recommendations", "pytest", "-q"], cwd=MS,
        title="Docker: pytest в контейнере recommendations")
    run(["docker", "compose", "exec", "-T", "marketplace", "pytest", "-q", "test_marketplace_integration.py"],
        cwd=MS, env={**ENV}, title="Docker: pytest в контейнере marketplace")
    run(["docker", "compose", "logs", "--no-color", "--tail", "15"], cwd=MS, title="docker compose logs")
    run(["docker", "compose", "down"], cwd=MS, title="docker compose down")


# ---------------------------------------------------------------- отчёт
def write_report(started: datetime) -> Path:
    lines = [
        "# Отчёт по ЛР3: Protocol Buffers и gRPC, микросервисы Recommendations + Marketplace\n",
        f"Сформирован автоматически скриптом `run_lab.py`: {started:%Y-%m-%d %H:%M:%S}, "
        f"{platform.platform()}, Python {platform.python_version()}.\n",
        "Все выводы ниже — реальные, получены при локальном запуске. Подробный порядок "
        "развёртывания — в [README.md](README.md).\n",
        "## Итоги прогона\n",
        "| Шаг | Результат |", "|---|---|",
    ]
    lines += [f"| {title} | {'OK' if ok else 'ОШИБКА'} |" for title, ok in summary]
    path = ROOT / "REPORT.md"
    path.write_text("\n".join(lines) + "\n" + "\n".join(report), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-docker", action="store_true", help="не запускать Docker Compose")
    args = parser.parse_args()
    started = datetime.now()

    step_env()
    if step_generate():
        step_part1_2()
        step_hello()
        step_stats()
        step_library()
        step_microservices()
    else:
        print("Генерация кода не удалась — остальные шаги пропущены.", flush=True)

    if args.no_docker:
        print("\nDocker-часть пропущена (--no-docker).")
    elif docker_available():
        step_docker()
    else:
        heading("7. Часть 6.4–6.5. Контейнеризация и Docker Compose")
        prose("Docker не найден или демон не запущен — шаг пропущен. Запустите Docker Desktop и повторите "
              "`python run_lab.py`, либо выполните команды из README вручную.")
        summary.append(("Docker Compose (пропущено: Docker недоступен)", False))

    path = write_report(started)
    failed = [title for title, ok in summary if not ok]
    print(f"\nОтчёт записан: {path}")
    print("Все шаги успешны." if not failed else "Шаги с ошибками: " + "; ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
