"""Версии окружения для отчёта."""
import platform
import sys

import fastapi
import google.protobuf
import grpc
import uvicorn

print("ОС:        ", platform.platform())
print("Python:    ", sys.version.split()[0])
print("grpcio:    ", grpc.__version__)
print("protobuf:  ", google.protobuf.__version__)
print("fastapi:   ", fastapi.__version__)
print("uvicorn:   ", uvicorn.__version__)
