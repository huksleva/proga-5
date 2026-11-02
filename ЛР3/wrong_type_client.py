"""Демонстрация ошибки: в метод передано сообщение ответа вместо сообщения запроса."""
import grpc
import helloworld_pb2
import helloworld_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = helloworld_pb2_grpc.GreeterStub(channel)
    # ОШИБКА: нужен MyNameRequest(name=...), а передан MyNameReply(message=...)
    wrong = stub.SayMyName(helloworld_pb2.MyNameReply(message="Heisenberg"), timeout=5)
    print(wrong.message)
    print("Вызов сработал: у MyNameReply и MyNameRequest поле 1 — строка, байты совпадают.")
