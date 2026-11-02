"""Сервис рекомендаций книг (gRPC)."""
import os
import random
from concurrent import futures

import grpc
import recommendations_pb2_grpc
from recommendations_pb2 import BookCategory, BookRecommendation, RecommendationResponse

BOOKS_BY_CATEGORY = {
    BookCategory.BOOK_CATEGORY_MYSTERY: [
        BookRecommendation(id=1, title="The Maltese Falcon"),
        BookRecommendation(id=2, title="Murder on the Orient Express"),
        BookRecommendation(id=3, title="The Hound of the Baskervilles"),
        BookRecommendation(id=4, title="The Name of the Rose"),
    ],
    BookCategory.BOOK_CATEGORY_SCIENCE_FICTION: [
        BookRecommendation(id=5, title="The Hitchhiker's Guide to the Galaxy"),
        BookRecommendation(id=6, title="Ender's Game"),
        BookRecommendation(id=7, title="Dune"),
        BookRecommendation(id=8, title="Solaris"),
    ],
    BookCategory.BOOK_CATEGORY_SELF_HELP: [
        BookRecommendation(id=9, title="The 7 Habits of Highly Effective People"),
        BookRecommendation(id=10, title="How to Win Friends and Influence People"),
        BookRecommendation(id=11, title="Man's Search for Meaning"),
    ],
}


class RecommendationService(recommendations_pb2_grpc.RecommendationsServicer):
    def Recommend(self, request, context):
        if request.max_results <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "max_results must be positive")
        if request.category == BookCategory.BOOK_CATEGORY_UNSPECIFIED:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "category is required")
        books = BOOKS_BY_CATEGORY.get(request.category)
        if books is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Category {request.category} not found")
        num_results = min(request.max_results, len(books))
        return RecommendationResponse(recommendations=random.sample(books, num_results))


def create_server(port: int = 50051) -> tuple[grpc.Server, int]:
    """Создаёт сервер. port=0 — выбрать свободный порт (удобно в тестах)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    recommendations_pb2_grpc.add_RecommendationsServicer_to_server(RecommendationService(), server)
    bound_port = server.add_insecure_port(f"[::]:{port}")
    return server, bound_port


if __name__ == "__main__":
    server, bound_port = create_server(int(os.getenv("PORT", "50051")))
    server.start()
    print(f"Recommendations service listening on {bound_port}", flush=True)
    server.wait_for_termination()
