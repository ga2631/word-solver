import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_settings():
    original_test_mode = settings.TEST_MODE
    original_show_daily = settings.SHOW_DAILY_WORD
    yield
    settings.TEST_MODE = original_test_mode
    settings.SHOW_DAILY_WORD = original_show_daily


def test_guess_word_success_plane_vs_apple():
    response = client.get("/api/v1/word/apple?guess=plane")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    expected = [
        (0, "p", "present"),
        (1, "l", "present"),
        (2, "a", "present"),
        (3, "n", "absent"),
        (4, "e", "correct"),
    ]
    for i, (slot, char, result) in enumerate(expected):
        assert data[i]["slot"] == slot
        assert data[i]["guess"] == char
        assert data[i]["result"] == result


def test_guess_word_exact_match():
    response = client.get("/api/v1/word/crane?guess=crane")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    for item in data:
        assert item["result"] == "correct"


def test_guess_word_duplicate_letters():
    response = client.get("/api/v1/word/apple?guess=paper")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    expected = [
        (0, "p", "present"),
        (1, "a", "present"),
        (2, "p", "correct"),
        (3, "e", "present"),
        (4, "r", "absent"),
    ]
    for i, (slot, char, result) in enumerate(expected):
        assert data[i]["slot"] == slot
        assert data[i]["guess"] == char
        assert data[i]["result"] == result


def test_guess_word_length_mismatch():
    response = client.get("/api/v1/word/apple?guess=cat")
    assert response.status_code == 400
    assert "does not match target word" in response.json()["detail"]


def test_guess_word_case_insensitivity():
    response = client.get("/api/v1/word/Apple?guess=CRANE")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert [item["guess"] for item in data] == ["c", "r", "a", "n", "e"]


def test_guess_word_test_mode_header():
    # 1. Disabled test mode
    settings.TEST_MODE = False
    settings.SHOW_DAILY_WORD = False
    res_disabled = client.get("/api/v1/word/apple?guess=crane")
    assert res_disabled.status_code == 200
    assert "X-Target-Word" not in res_disabled.headers

    # 2. Enabled test mode
    settings.TEST_MODE = True
    res_enabled = client.get("/api/v1/word/apple?guess=crane")
    assert res_enabled.status_code == 200
    assert res_enabled.headers.get("X-Target-Word") == "apple"
