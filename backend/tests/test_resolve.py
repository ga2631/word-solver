import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import httpx

from app.core.config import settings
from app.main import app
from app.schemas.resolve import (
    ResolveMode,
    ResolveRequest,
)
from app.schemas.wordle import GuessResult, ResultKind
from app.services.daily_store import DailyWordStore
from app.services.resolver_service import ResolverService
from app.services.wordle_service import WordleService

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_daily_store():
    orig_test_mode = settings.TEST_MODE
    settings.TEST_MODE = True
    DailyWordStore.load_store()
    yield
    settings.TEST_MODE = orig_test_mode
    DailyWordStore.load_store()


# ==========================================
# Unit Tests for Solver Heuristics & Matching
# ==========================================


def test_matches_feedback_all_correct():
    feedback = [
        GuessResult(slot=0, guess="a", result=ResultKind.CORRECT),
        GuessResult(slot=1, guess="p", result=ResultKind.CORRECT),
        GuessResult(slot=2, guess="p", result=ResultKind.CORRECT),
        GuessResult(slot=3, guess="l", result=ResultKind.CORRECT),
        GuessResult(slot=4, guess="e", result=ResultKind.CORRECT),
    ]
    assert ResolverService.matches_feedback("apple", "apple", feedback) is True
    assert ResolverService.matches_feedback("apply", "apple", feedback) is False


def test_matches_feedback_with_absent_and_present():
    feedback = [
        GuessResult(slot=0, guess="c", result=ResultKind.ABSENT),
        GuessResult(slot=1, guess="r", result=ResultKind.ABSENT),
        GuessResult(slot=2, guess="a", result=ResultKind.PRESENT),
        GuessResult(slot=3, guess="n", result=ResultKind.ABSENT),
        GuessResult(slot=4, guess="e", result=ResultKind.CORRECT),
    ]
    assert ResolverService.matches_feedback("apple", "crane", feedback) is True
    assert ResolverService.matches_feedback("crane", "crane", feedback) is False
    assert ResolverService.matches_feedback("blade", "crane", feedback) is False
    assert ResolverService.matches_feedback("camel", "crane", feedback) is False


def test_matches_feedback_duplicate_letters():
    feedback = WordleService.evaluate_guess(target="apple", guess="paper")
    assert ResolverService.matches_feedback("apple", "paper", feedback) is True
    assert ResolverService.matches_feedback("paper", "paper", feedback) is False


def test_score_word():
    score_crane = ResolverService.score_word("crane")
    score_fuzzy = ResolverService.score_word("fuzzy")
    assert score_crane > score_fuzzy


def test_choose_initial_word_default():
    candidates = WordleService.get_words_by_length(5)
    start = ResolverService.choose_initial_word(size=5, candidates=candidates)
    assert start == "crane"


def test_choose_initial_word_custom():
    candidates = WordleService.get_words_by_length(5)
    start = ResolverService.choose_initial_word(
        size=5, candidates=candidates, custom_starting_word="slate"
    )
    assert start == "slate"


def test_choose_initial_word_custom_size_mismatch():
    candidates = WordleService.get_words_by_length(5)
    with pytest.raises(ValueError, match="does not match puzzle size"):
        ResolverService.choose_initial_word(
            size=5, candidates=candidates, custom_starting_word="orange"
        )


# ==========================================
# Resolver Service Core Solving Tests
# ==========================================


@pytest.mark.anyio
async def test_resolver_service_solve_word_mode_apple():
    req = ResolveRequest(
        mode=ResolveMode.WORD,
        word="apple",
    )
    res = await ResolverService.resolve(req)
    assert res.success is True
    assert res.target_word == "apple"
    assert res.mode == ResolveMode.WORD
    assert res.starting_word == "crane"
    assert len(res.steps) >= 1
    last_step = res.steps[-1]
    assert last_step.guess == "apple"
    assert all(r.result == ResultKind.CORRECT for r in last_step.results)


@pytest.mark.anyio
async def test_resolver_service_solve_word_mode_multiple_words():
    test_words = ["tiger", "piano", "green", "speed", "water", "flame"]
    for target in test_words:
        req = ResolveRequest(
            mode=ResolveMode.WORD,
            word=target,
        )
        res = await ResolverService.resolve(req)
        assert res.success is True
        assert res.target_word == target
        assert len(res.steps) <= 15


@pytest.mark.anyio
async def test_resolver_service_solve_daily_mode():
    DailyWordStore.set_word(word="ocean", size=5)
    req = ResolveRequest(
        mode=ResolveMode.DAILY,
        size=5,
    )
    res = await ResolverService.resolve(req)
    assert res.success is True
    assert res.target_word == "ocean"
    assert res.mode == ResolveMode.DAILY


@pytest.mark.anyio
async def test_resolver_service_solve_random_mode_with_seed():
    req = ResolveRequest(
        mode=ResolveMode.RANDOM,
        size=5,
        seed="test-seed-42",
    )
    res = await ResolverService.resolve(req)
    assert res.success is True
    assert res.mode == ResolveMode.RANDOM
    assert res.target_word is not None
    assert len(res.target_word) == 5


@pytest.mark.anyio
async def test_resolver_service_solve_different_length():
    req = ResolveRequest(
        mode=ResolveMode.WORD,
        word="banana",
    )
    res = await ResolverService.resolve(req)
    assert res.success is True
    assert res.target_word == "banana"
    assert len(res.steps[-1].results) == 6


@pytest.mark.anyio
async def test_resolver_service_custom_starting_word():
    req = ResolveRequest(
        mode=ResolveMode.WORD,
        word="tiger",
        starting_word="slate",
    )
    res = await ResolverService.resolve(req)
    assert res.success is True
    assert res.starting_word == "slate"
    assert res.steps[0].guess == "slate"


@pytest.mark.anyio
async def test_resolver_remote_when_test_mode_false():
    mock_responses = [
        # Step 1: guess 'crane'
        [
            {"slot": 0, "guess": "c", "result": "absent"},
            {"slot": 1, "guess": "r", "result": "absent"},
            {"slot": 2, "guess": "a", "result": "present"},
            {"slot": 3, "guess": "n", "result": "absent"},
            {"slot": 4, "guess": "e", "result": "correct"},
        ],
        # Step 2: guess 'apple'
        [
            {"slot": 0, "guess": "a", "result": "correct"},
            {"slot": 1, "guess": "p", "result": "correct"},
            {"slot": 2, "guess": "p", "result": "correct"},
            {"slot": 3, "guess": "l", "result": "correct"},
            {"slot": 4, "guess": "e", "result": "correct"},
        ],
    ]

    call_count = 0

    async def mock_get(url, params=None):
        nonlocal call_count
        resp_data = (
            mock_responses[call_count]
            if call_count < len(mock_responses)
            else mock_responses[-1]
        )
        call_count += 1
        return httpx.Response(200, json=resp_data)

    settings.TEST_MODE = False
    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        req = ResolveRequest(
            mode=ResolveMode.DAILY,
            size=5,
        )
        res = await ResolverService.resolve(req)
        assert res.success is True
        assert len(res.steps) == 2


# ==========================================
# API Endpoint Integration Tests (GET /resolve)
# ==========================================


def test_api_resolve_get_word_mode():
    response = client.get("/api/v1/resolve?mode=word&word=tiger")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["target_word"] == "tiger"
    assert data["mode"] == "word"
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) >= 1


def test_api_resolve_get_daily_mode():
    DailyWordStore.set_word(word="plant", size=5)
    response = client.get("/api/v1/resolve?mode=daily&size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["target_word"] == "plant"
    assert data["mode"] == "daily"


def test_api_resolve_get_random_mode():
    response = client.get("/api/v1/resolve?mode=random&size=5&seed=fixed-seed")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "random"
    assert data["target_word"] is not None


def test_api_resolve_missing_word_in_word_mode():
    response = client.get("/api/v1/resolve?mode=word")
    assert response.status_code == 400
    assert "required when mode is 'word'" in response.json()["detail"]


def test_api_resolve_invalid_size():
    response = client.get("/api/v1/resolve?mode=daily&size=0")
    assert response.status_code == 422  # Pydantic validation error for ge=1


def test_api_resolve_nonexistent_size():
    response = client.get("/api/v1/resolve?mode=daily&size=49")
    assert response.status_code == 400 or response.status_code == 404


def test_api_solver_starting_word():
    response = client.get("/api/v1/solver/starting-word?size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == 5
    assert data["starting_word"] == "crane"
    assert data["total_candidates"] > 0

    # Test size 4
    response_4 = client.get("/api/v1/solver/starting-word?size=4")
    assert response_4.status_code == 200
    assert response_4.json()["starting_word"] == "roam"


def test_api_solver_next_guess():
    payload = {
        "size": 5,
        "history": [
            {
                "guess": "crane",
                "feedback": [
                    {"slot": 0, "guess": "c", "result": "absent"},
                    {"slot": 1, "guess": "r", "result": "correct"},
                    {"slot": 2, "guess": "a", "result": "present"},
                    {"slot": 3, "guess": "n", "result": "absent"},
                    {"slot": 4, "guess": "e", "result": "absent"},
                ],
            }
        ],
    }
    response = client.post("/api/v1/solver/next-guess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_guess"] is not None
    assert len(data["next_guess"]) == 5
    assert data["remaining_candidates_count"] > 0
    assert "c" in data["eliminated_letters"]
    assert "n" in data["eliminated_letters"]
    assert "e" in data["eliminated_letters"]
    assert data["is_exhausted"] is False
    assert "execution_time_ms" in data

