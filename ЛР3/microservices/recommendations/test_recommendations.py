import grpc
import pytest
from recommendations import RecommendationService, create_server
from recommendations_pb2 import BookCategory, RecommendationRequest
from recommendations_pb2_grpc import RecommendationsStub


def test_recommend_returns_requested_number():
    service = RecommendationService()
    request = RecommendationRequest(
        user_id=1, category=BookCategory.BOOK_CATEGORY_MYSTERY, max_results=2
    )
    response = service.Recommend(request, context=None)
    assert len(response.recommendations) == 2


def test_recommend_is_limited_by_catalog_size():
    service = RecommendationService()
    request = RecommendationRequest(
        user_id=1, category=BookCategory.BOOK_CATEGORY_SELF_HELP, max_results=100
    )
    response = service.Recommend(request, context=None)
    assert len(response.recommendations) == 3


@pytest.fixture
def stub():
    server, port = create_server(port=0)
    server.start()
    with grpc.insecure_channel(f"localhost:{port}") as channel:
        yield RecommendationsStub(channel)
    server.stop(grace=None)


@pytest.mark.parametrize(
    ("category", "max_results", "expected_code"),
    [
        (BookCategory.BOOK_CATEGORY_MYSTERY, 0, grpc.StatusCode.INVALID_ARGUMENT),
        (BookCategory.BOOK_CATEGORY_UNSPECIFIED, 1, grpc.StatusCode.INVALID_ARGUMENT),
        (99, 1, grpc.StatusCode.NOT_FOUND),   # неизвестное значение enum допустимо в proto3
    ],
)
def test_errors(stub, category, max_results, expected_code):
    request = RecommendationRequest(user_id=1, category=category, max_results=max_results)
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.Recommend(request, timeout=2)
    assert exc_info.value.code() == expected_code
