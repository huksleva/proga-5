"""Сервер LibraryService: коды ошибок, дедлайны, метаданные, reflection."""
import time
from collections import Counter
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from library.v1 import library_pb2, library_service_pb2, library_service_pb2_grpc

API_TOKEN = "secret-token"   # в реальном проекте — из переменной окружения или хранилища секретов


def make_books() -> dict[int, library_pb2.Book]:
    data = [
        (1, "Solaris", library_pb2.GENRE_FICTION, "Stanisław Lem"),
        (2, "A Brief History of Time", library_pb2.GENRE_SCIENCE, "Stephen Hawking"),
        (3, "The Guns of August", library_pb2.GENRE_HISTORY, "Barbara W. Tuchman"),
        (4, "Roadside Picnic", library_pb2.GENRE_FICTION, "Arkady and Boris Strugatsky"),
    ]
    books = {}
    for book_id, title, genre, author in data:
        book = library_pb2.Book(id=book_id, title=title, genre=genre)
        book.authors.add(name=author)
        books[book_id] = book
    return books


class LibraryService(library_service_pb2_grpc.LibraryServiceServicer):
    def __init__(self) -> None:
        self._books = make_books()

    def GetBook(self, request, context):
        metadata = dict(context.invocation_metadata())
        request_id = metadata.get("x-request-id", "-")
        # Завершающие метаданные клиент получит вместе с ответом или ошибкой
        context.set_trailing_metadata([("x-request-id", request_id), ("x-served-by", "library-1")])
        if request.id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id must be positive")
        book = self._books.get(request.id)
        if book is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Book {request.id} not found")
        return book

    def ListBooks(self, request, context):
        for book in self._books.values():
            if request.genre in (library_pb2.GENRE_UNSPECIFIED, book.genre):
                yield book

    def BuildReport(self, request, context):
        metadata = dict(context.invocation_metadata())
        if metadata.get("authorization") != f"Bearer {API_TOKEN}":
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid token")
        finish_at = time.monotonic() + request.work_seconds
        while time.monotonic() < finish_at:        # имитация долгой работы
            if not context.is_active():            # дедлайн истёк или клиент отменил вызов
                print("BuildReport: клиент больше не ждёт, прекращаем работу", flush=True)
                return library_service_pb2.Report()
            time.sleep(0.05)
        by_genre = Counter(library_pb2.Genre.Name(book.genre) for book in self._books.values())
        return library_service_pb2.Report(total_books=len(self._books), books_by_genre=by_genre)


def serve(port: int = 50052) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_service_pb2_grpc.add_LibraryServiceServicer_to_server(LibraryService(), server)
    service_names = (
        library_service_pb2.DESCRIPTOR.services_by_name["LibraryService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server


if __name__ == "__main__":
    serve().wait_for_termination()
