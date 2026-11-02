"""Генерация Python-кода из всех .proto-файлов (аналог ячеек !protoc из ноутбука).

Запуск из каталога ЛР3:  python generate.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def protoc(cwd: Path, include: str, files: list[str], grpc_out: bool) -> None:
    cmd = [sys.executable, "-m", "grpc_tools.protoc", "-I", include,
           "--python_out=.", "--pyi_out=."]
    if grpc_out:
        cmd.append("--grpc_python_out=.")
    cmd += files
    print("$", "python -m grpc_tools.protoc", *cmd[3:], flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    # Часть 1-2: сообщения без gRPC
    protoc(ROOT, "protos",
           ["protos/library/v1/library.proto", "protos/encoding_demo.proto",
            "protos/evolution/v1/user.proto", "protos/evolution/v2/user.proto"],
           grpc_out=False)
    # Части 3-5: сервисы
    protoc(ROOT, "protos",
           ["protos/helloworld.proto", "protos/stats.proto",
            "protos/library/v1/library_service.proto"],
           grpc_out=True)
    # Часть 6: общий контракт кладём в каждый микросервис
    for service in ("recommendations", "marketplace"):
        protoc(ROOT / "microservices" / service, "../protos",
               ["../protos/recommendations.proto"], grpc_out=True)
    print("Готово.")


if __name__ == "__main__":
    main()
