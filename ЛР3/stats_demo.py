"""Часть 4. Потоковые вызовы: сервер запускается в этом же процессе."""
import time

import grpc
import stats_pb2
import stats_pb2_grpc
import stats_server

stats_grpc_server = stats_server.serve(port=50053)
stats_channel = grpc.insecure_channel("localhost:50053")
stats_stub = stats_pb2_grpc.StatsStub(stats_channel)
print("Сервер Stats запущен")

print("\n--- Серверный поток: Countdown(5) ---")
start = time.monotonic()
for reply in stats_stub.Countdown(stats_pb2.CountdownRequest(start=5), timeout=10):
    print(f"{time.monotonic() - start:4.1f} с: {reply.value}")


def numbers(values):
    for value in values:
        yield stats_pb2.Number(value=value)


print("\n--- Клиентский поток: Sum ---")
summary = stats_stub.Sum(numbers([1, 2, 3.5, 10]), timeout=5)
print(f"Сумма {summary.total} из {summary.count} чисел")


def slow_numbers(values, delay=0.3):
    for value in values:
        print(f"  → отправляем {value}")
        yield stats_pb2.Number(value=value)
        time.sleep(delay)


print("\n--- Двунаправленный поток: RunningAverage ---")
for reply in stats_stub.RunningAverage(slow_numbers([10, 20, 30, 40]), timeout=10):
    print(f"  ← среднее после {reply.count} чисел: {reply.average}")

print("\n--- Отмена потока клиентом и INVALID_ARGUMENT ---")
responses = stats_stub.Countdown(stats_pb2.CountdownRequest(start=20), timeout=10)
try:
    for reply in responses:
        print(reply.value, end=" ", flush=True)
        if reply.value == 17:
            responses.cancel()                  # больше не нужно
except grpc.RpcError as error:
    print("\nВызов завершён:", error.code())

try:
    list(stats_stub.Countdown(stats_pb2.CountdownRequest(start=-1), timeout=5))
except grpc.RpcError as error:
    print("Ошибка:", error.code(), "—", error.details())

stats_channel.close()
stats_grpc_server.stop(grace=None)
print("Сервер Stats остановлен")
