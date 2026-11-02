"""Интеграционные тесты: нужны запущенные Marketplace и Recommendations."""
import json
import os
from urllib.request import urlopen

BASE_URL = os.getenv("MARKETPLACE_URL", "http://localhost:8000")


def test_homepage_renders_three_books():
    with urlopen(f"{BASE_URL}/", timeout=5) as response:
        page = response.read().decode("utf-8")
    assert "<title>Online Books For You</title>" in page
    assert page.count("<li>") == 3


def test_api_returns_recommendations():
    url = f"{BASE_URL}/api/v1/recommendations?user_id=1&category=science_fiction&max_results=2"
    with urlopen(url, timeout=5) as response:
        assert response.status == 200
        books = json.load(response)
    assert len(books) == 2
    assert set(books[0]) == {"id", "title"}
