"""Часть 5. Метаданные, коды статуса, дедлайны, grpc.aio, reflection."""
import asyncio
import time

import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

import library_server
from library.v1 import library_pb2, library_service_pb2, library_service_pb2_grpc

library_grpc_server = library_server.serve(port=50052)
library_channel = grpc.insecure_channel("localhost:50052")
library_stub = library_service_pb2_grpc.LibraryServiceStub(library_channel)
print("Сервер LibraryService запущен")

print("\n--- 5.1 Метаданные ---")
book, call = library_stub.GetBook.with_call(
    library_service_pb2.GetBookRequest(id=1),
    metadata=[("x-request-id", "req-42")],
    timeout=2,
)
print(book.title, "—", book.authors[0].name)
print("Метаданные ответа:", dict(call.trailing_metadata()))

print("\n--- 5.2 Коды статуса ---")
for book_id in (2, 999, 0):
    try:
        found = library_stub.GetBook(library_service_pb2.GetBookRequest(id=book_id), timeout=2)
        print(f"id={book_id}: {found.title}")
    except grpc.RpcError as error:
        print(f"id={book_id}: {error.code().name} — {error.details()}")

for found in library_stub.ListBooks(
        library_service_pb2.ListBooksRequest(genre=library_pb2.GENRE_FICTION), timeout=5):
    print(found.id, found.title)

print("\n--- 5.3 Аутентификация через метаданные и дедлайны ---")
auth = [("authorization", f"Bearer {library_server.API_TOKEN}")]
scenarios = [
    ("без токена", [], 1.0, 5),
    ("короткий дедлайн", auth, 2.0, 0.5),
    ("успех", auth, 1.0, 5),
]
for title, metadata, work_seconds, timeout in scenarios:
    started = time.monotonic()
    try:
        report = library_stub.BuildReport(
            library_service_pb2.BuildReportRequest(work_seconds=work_seconds),
            metadata=metadata,
            timeout=timeout,
        )
        result = f"OK: {report.total_books} книги, {dict(report.books_by_genre)}"
    except grpc.RpcError as error:
        result = f"{error.code().name} — {error.details()}"
    print(f"{title:<18} {time.monotonic() - started:4.1f} с  {result}")


print("\n--- 5.4 Асинхронный клиент grpc.aio ---")
async def fetch_many(ids: list[int]) -> None:
    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = library_service_pb2_grpc.LibraryServiceStub(channel)
        calls = [stub.GetBook(library_service_pb2.GetBookRequest(id=i), timeout=2) for i in ids]
        results = await asyncio.gather(*calls, return_exceptions=True)
    for book_id, result in zip(ids, results):
        if isinstance(result, grpc.aio.AioRpcError):
            print(f"id={book_id}: {result.code().name}")
        else:
            print(f"id={book_id}: {result.title}")


asyncio.run(fetch_many([1, 2, 3, 4, 42]))

print("\n--- 5.5 Server reflection (аналог grpcurl list) ---")
reflection_stub = reflection_pb2_grpc.ServerReflectionStub(library_channel)
request = reflection_pb2.ServerReflectionRequest(list_services="")
for response in reflection_stub.ServerReflectionInfo(iter([request])):
    for service in response.list_services_response.service:
        print(service.name)

library_channel.close()
library_grpc_server.stop(grace=None)
print("\nСервер LibraryService остановлен")
