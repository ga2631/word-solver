import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app
from app.services.wordle_service import WordleService

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_settings():
    original_test_mode = settings.TEST_MODE
    yield
    settings.TEST_MODE = original_test_mode


def test_random_word_success_default_size():
    response = client.get("/api/v1/random?guess=crane")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5

    expected_chars = ["c", "r", "a", "n", "e"]
    for i, item in enumerate(data):
        assert item["slot"] == i
        assert item["guess"] == expected_chars[i]
        assert item["result"] in ["absent", "correct", "present"]


def test_random_word_custom_size():
    response = client.get("/api/v1/random?guess=orange&size=6")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    expected_chars = ["o", "r", "a", "n", "g", "e"]
    for i, item in enumerate(data):
        assert item["slot"] == i
        assert item["guess"] == expected_chars[i]
        assert item["result"] in ["absent", "correct", "present"]


def test_random_word_length_mismatch():
    response = client.get("/api/v1/random?guess=cat&size=5")
    assert response.status_code == 400
    assert "does not match size" in response.json()["detail"]


def test_random_word_with_seed_deterministic():
    settings.TEST_MODE = True
    seed_val = "custom-test-seed-42"

    res1 = client.get(f"/api/v1/random?guess=crane&size=5&seed={seed_val}")
    res2 = client.get(f"/api/v1/random?guess=crane&size=5&seed={seed_val}")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.headers.get("X-Random-Word") == res2.headers.get("X-Random-Word")
    assert res1.json() == res2.json()


def test_random_word_test_mode_header():
    # 1. TEST_MODE = False
    settings.TEST_MODE = False
    res_disabled = client.get("/api/v1/random?guess=crane&size=5")
    assert res_disabled.status_code == 200
    assert "X-Random-Word" not in res_disabled.headers

    # 2. TEST_MODE = True
    settings.TEST_MODE = True
    res_enabled = client.get("/api/v1/random?guess=crane&size=5")
    assert res_enabled.status_code == 200
    assert "X-Random-Word" in res_enabled.headers
    assert len(res_enabled.headers["X-Random-Word"]) == 5


def test_service_get_random_word_seeded():
    word1 = WordleService.get_random_word(size=5, seed="seed-abc")
    word2 = WordleService.get_random_word(size=5, seed="seed-abc")
    assert word1 == word2
    assert len(word1) == 5


def test_random_word_from_dictionary():
    dict_words_5 = WordleService.get_words_by_length(5)
    for _ in range(20):
        word = WordleService.get_random_word(size=5)
        assert word in dict_words_5
        assert len(word) == 5


def test_api_get_random_word_endpoint():
    # 1. Default size
    response = client.get("/api/v1/random/word")
    assert response.status_code == 200
    data = response.json()
    assert "word" in data
    assert len(data["word"]) == 5
    assert data["size"] == 5
    dict_words = WordleService.get_words_by_length(5)
    assert data["word"] in dict_words

    # 2. Custom size with seed
    res2 = client.get("/api/v1/random/word?size=6&seed=seed123")
    assert res2.status_code == 200
    d2 = res2.json()
    assert len(d2["word"]) == 6
    assert d2["size"] == 6
    assert d2["seed"] == "seed123"

    res3 = client.get("/api/v1/random/word?size=6&seed=seed123")
    assert res3.json()["word"] == d2["word"]

