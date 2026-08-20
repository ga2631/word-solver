import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_get_categories():
    response = client.get("/api/v1/words/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert "tech" in categories
    assert "nature" in categories


def test_generate_words_get():
    response = client.get("/api/v1/words/generate?category=tech&count=3")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["words"]) == 3
    for item in data["words"]:
        assert item["category"] == "tech"
        assert len(item["word"]) > 0


def test_generate_words_post():
    payload = {
        "category": "science",
        "count": 4,
        "min_length": 3,
        "max_length": 12,
    }
    response = client.post("/api/v1/words/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["words"]) == 4


def test_generate_words_invalid_lengths():
    response = client.get("/api/v1/words/generate?min_length=15&max_length=5")
    assert response.status_code == 400


def test_analyze_word():
    payload = {"word": "radar"}
    response = client.post("/api/v1/words/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["word"] == "radar"
    assert data["length"] == 5
    assert data["is_palindrome"] is True
    assert data["reversed"] == "radar"
    assert data["vowels_count"] == 2
    assert data["consonants_count"] == 3
