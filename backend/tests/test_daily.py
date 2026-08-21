import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app
from app.schemas.wordle import ResultKind
from app.services.daily_store import DailyWordStore
from app.services.wordle_service import WordleService

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_daily_store():
    """Ensure clean store state and default settings before each test."""
    original_test_mode = settings.TEST_MODE
    DailyWordStore.load_store()
    yield
    settings.TEST_MODE = original_test_mode
    DailyWordStore.load_store()


def test_daily_word_success_default_size():
    response = client.get("/api/v1/daily?guess=crane")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5

    expected_chars = ["c", "r", "a", "n", "e"]
    for i, item in enumerate(data):
        assert item["slot"] == i
        assert item["guess"] == expected_chars[i]
        assert item["result"] in ["absent", "correct", "present"]


def test_daily_word_custom_size():
    response = client.get("/api/v1/daily?guess=orange&size=6")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    expected_chars = ["o", "r", "a", "n", "g", "e"]
    for i, item in enumerate(data):
        assert item["slot"] == i
        assert item["guess"] == expected_chars[i]
        assert item["result"] in ["absent", "correct", "present"]


def test_daily_word_length_mismatch():
    # guess is length 3, but size defaults to 5
    response = client.get("/api/v1/daily?guess=cat")
    assert response.status_code == 400
    assert "does not match size" in response.json()["detail"]

    # guess is length 5, but size is specified as 6
    response = client.get("/api/v1/daily?guess=crane&size=6")
    assert response.status_code == 400
    assert "does not match size" in response.json()["detail"]


def test_daily_word_uppercase_handling():
    response = client.get("/api/v1/daily?guess=CRANE&size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert [item["guess"] for item in data] == ["c", "r", "a", "n", "e"]


def test_daily_store_set_static_word_and_guess():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Set a custom static word for today
    DailyWordStore.set_word(target_date=today, word="tiger", size=5)

    response = client.get("/api/v1/daily?guess=tiger&size=5")
    assert response.status_code == 200
    data = response.json()
    # Since guess == target ("tiger"), all slots should be correct
    for item in data:
        assert item["result"] == "correct"


def test_daily_store_custom_dates():
    DailyWordStore.set_word(target_date="2030-01-01", word="piano", size=5)
    assert DailyWordStore.get_word(target_date="2030-01-01", size=5) == "piano"
    assert WordleService.get_daily_word(size=5, target_date="2030-01-01") == "piano"


def test_test_flag_shows_daily_word_in_headers():
    # 1. Disabled test flag -> No header
    settings.TEST_MODE = False
    res_disabled = client.get("/api/v1/daily?guess=crane&size=5")
    assert res_disabled.status_code == 200
    assert "X-Daily-Word" not in res_disabled.headers

    # 2. Enabled test flag -> Header present
    settings.TEST_MODE = True
    res_enabled = client.get("/api/v1/daily?guess=crane&size=5")
    assert res_enabled.status_code == 200
    assert "X-Daily-Word" in res_enabled.headers
    assert res_enabled.headers["X-Daily-Word"] == "crane"


def test_wordle_evaluation_exact_match():
    results = WordleService.evaluate_guess(target="apple", guess="apple")
    assert len(results) == 5
    for r in results:
        assert r.result == ResultKind.CORRECT


def test_wordle_evaluation_duplicates_paper_vs_apple():
    # target: apple, guess: paper
    # slot 0: p -> present (1 p remaining)
    # slot 1: a -> present
    # slot 2: p -> correct (exact match)
    # slot 3: e -> present
    # slot 4: r -> absent
    results = WordleService.evaluate_guess(target="apple", guess="paper")
    expected = [
        (0, "p", ResultKind.PRESENT),
        (1, "a", ResultKind.PRESENT),
        (2, "p", ResultKind.CORRECT),
        (3, "e", ResultKind.PRESENT),
        (4, "r", ResultKind.ABSENT),
    ]
    for i, (slot, char, status) in enumerate(expected):
        assert results[i].slot == slot
        assert results[i].guess == char
        assert results[i].result == status


def test_wordle_evaluation_plane_vs_apple():
    # target: apple, guess: plane
    # slot 0: p -> present
    # slot 1: l -> present
    # slot 2: a -> present
    # slot 3: n -> absent
    # slot 4: e -> correct
    results = WordleService.evaluate_guess(target="apple", guess="plane")
    expected = [
        (0, "p", ResultKind.PRESENT),
        (1, "l", ResultKind.PRESENT),
        (2, "a", ResultKind.PRESENT),
        (3, "n", ResultKind.ABSENT),
        (4, "e", ResultKind.CORRECT),
    ]
    for i, (slot, char, status) in enumerate(expected):
        assert results[i].slot == slot
        assert results[i].guess == char
        assert results[i].result == status


def test_daily_word_fallback_deterministic_when_not_in_store():
    # Date not in store
    word1 = WordleService.get_daily_word(size=5, target_date="2099-12-31")
    word2 = WordleService.get_daily_word(size=5, target_date="2099-12-31")
    assert word1 == word2
    assert len(word1) == 5
