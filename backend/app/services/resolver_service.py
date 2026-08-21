import logging
from typing import Dict, List, Optional
import httpx
from app.core.config import settings
from app.schemas.resolve import (
    ResolveMode,
    ResolveRequest,
    ResolveResponse,
    ResolveStep,
)
from app.schemas.wordle import GuessResult, ResultKind
from app.services.wordle_service import WordleService

logger = logging.getLogger(__name__)

# Standard English letter frequencies for optimal information gain
ENGLISH_LETTER_FREQ: Dict[str, float] = {
    "e": 12.02,
    "t": 9.10,
    "a": 8.12,
    "o": 7.68,
    "i": 7.31,
    "n": 6.95,
    "s": 6.28,
    "r": 6.02,
    "h": 5.92,
    "d": 4.32,
    "l": 3.98,
    "u": 2.88,
    "c": 2.71,
    "m": 2.61,
    "f": 2.30,
    "y": 2.11,
    "w": 2.09,
    "g": 2.03,
    "p": 1.82,
    "b": 1.49,
    "v": 1.11,
    "k": 0.69,
    "x": 0.17,
    "q": 0.11,
    "j": 0.10,
    "z": 0.07,
}


class ResolverService:
    @staticmethod
    def score_word(word: str) -> float:
        """
        Calculate an information-gain score for a word based on
        frequencies of its unique characters.
        """
        unique_letters = set(word.lower())
        return sum(ENGLISH_LETTER_FREQ.get(char, 0.0) for char in unique_letters)

    @staticmethod
    def matches_feedback(
        candidate: str,
        guess: str,
        feedback: List[GuessResult],
    ) -> bool:
        """
        Check if a candidate word satisfies the feedback returned for a guess.
        Handles exact position matches ('correct'), misplaced letters ('present'),
        and absent letters ('absent'), correctly accounting for duplicate letters.
        """
        n = len(guess)
        if len(candidate) != n:
            return False

        candidate_lower = candidate.lower()
        guess_lower = guess.lower()

        correct_or_present_counts: Dict[str, int] = {}
        has_absent: Dict[str, bool] = {}

        # 1. Positional checks
        for item in feedback:
            slot = item.slot
            char = item.guess.lower()
            res = item.result

            if res == ResultKind.CORRECT:
                if candidate_lower[slot] != char:
                    return False
                correct_or_present_counts[char] = (
                    correct_or_present_counts.get(char, 0) + 1
                )
            elif res == ResultKind.PRESENT:
                # Present means letter IS in the word, but NOT in this slot
                if candidate_lower[slot] == char:
                    return False
                correct_or_present_counts[char] = (
                    correct_or_present_counts.get(char, 0) + 1
                )
            elif res == ResultKind.ABSENT:
                # Absent in this slot means candidate cannot have this char in this slot
                if candidate_lower[slot] == char:
                    return False
                has_absent[char] = True

        # 2. Count candidate character frequencies
        cand_char_counts: Dict[str, int] = {}
        for c in candidate_lower:
            cand_char_counts[c] = cand_char_counts.get(c, 0) + 1

        # 3. Verify letter counts for correct/present letters
        for char, min_count in correct_or_present_counts.items():
            actual_count = cand_char_counts.get(char, 0)
            if has_absent.get(char, False):
                # Letter appeared as absent in other slots -> count is exact
                if actual_count != min_count:
                    return False
            else:
                # Letter had no absent feedback -> count is at least min_count
                if actual_count < min_count:
                    return False

        # 4. Verify letters that were only absent never appear
        for char in has_absent:
            if char not in correct_or_present_counts:
                if char in cand_char_counts:
                    return False

        return True

    @classmethod
    def choose_initial_word(
        cls,
        size: int,
        candidates: List[str],
        custom_starting_word: Optional[str] = None,
    ) -> str:
        """
        Choose the initial guess word.
        Uses custom starting word if provided, otherwise 'crane' for 5-letter words
        or the highest-scoring candidate for any word size.
        """
        if custom_starting_word:
            clean_word = custom_starting_word.strip().lower()
            if len(clean_word) != size:
                raise ValueError(
                    f"Starting word '{custom_starting_word}' length ({len(clean_word)}) "
                    f"does not match puzzle size ({size})"
                )
            return clean_word

        if size == 5 and settings.DEFAULT_SOLVER_START_WORD:
            start = settings.DEFAULT_SOLVER_START_WORD.strip().lower()
            if len(start) == 5 and (not candidates or start in candidates):
                return start

        if not candidates:
            raise ValueError(f"No dictionary candidates available for size {size}")

        # Pick candidate with the highest information score
        sorted_candidates = sorted(candidates, key=cls.score_word, reverse=True)
        return sorted_candidates[0]

    @classmethod
    async def _evaluate_remote(
        cls,
        client: httpx.AsyncClient,
        api_url: str,
        mode: ResolveMode,
        guess: str,
        size: int,
        word: Optional[str] = None,
        seed: Optional[str] = None,
    ) -> List[GuessResult]:
        """
        Query an external or remote Wordle API endpoint.
        """
        clean_url = api_url.rstrip("/")

        if mode == ResolveMode.DAILY:
            endpoint = f"{clean_url}/daily"
            params = {"guess": guess, "size": size}
            res = await client.get(endpoint, params=params)
        elif mode == ResolveMode.RANDOM:
            endpoint = f"{clean_url}/random"
            params = {"guess": guess, "size": size}
            if seed is not None:
                params["seed"] = str(seed)
            res = await client.get(endpoint, params=params)
        elif mode == ResolveMode.WORD:
            if not word:
                raise ValueError("Target word is required for 'word' mode")
            endpoint = f"{clean_url}/word/{word.strip().lower()}"
            params = {"guess": guess}
            res = await client.get(endpoint, params=params)
        else:
            raise ValueError(f"Unsupported resolve mode: {mode}")

        if res.status_code != 200:
            raise RuntimeError(
                f"External API error ({res.status_code}): {res.text}"
            )

        data = res.json()
        return [
            GuessResult(
                slot=item["slot"],
                guess=item["guess"],
                result=ResultKind(item["result"]),
            )
            for item in data
        ]

    @classmethod
    async def resolve(cls, request: ResolveRequest) -> ResolveResponse:
        """
        Execute Wordle solver following the pseudo-code and information theory heuristics.
        Supports both internal offline solving and remote API querying.
        """
        mode = request.mode
        size = request.size
        target_word_param = request.word.strip().lower() if request.word else None

        # Determine puzzle size from target word if in 'word' mode
        if mode == ResolveMode.WORD:
            if not target_word_param:
                raise ValueError("The 'word' field is required when mode is 'word'")
            size = len(target_word_param)

        # Load dictionary candidates
        try:
            candidates = list(WordleService.get_words_by_length(size))
        except FileNotFoundError:
            raise ValueError(f"No dictionary available for word length {size}")

        if not candidates:
            raise ValueError(f"No dictionary candidates found for size {size}")

        # Choose initial guess
        current_guess = cls.choose_initial_word(
            size=size,
            candidates=candidates,
            custom_starting_word=request.starting_word,
        )
        starting_word = current_guess

        # Determine evaluation mode based on TEST_MODE setting:
        # TEST_MODE=True -> Local internal evaluation
        # TEST_MODE=False -> Remote API evaluation at settings.VOTEE_API_BASE_URL
        use_remote_api = not settings.TEST_MODE

        internal_target: Optional[str] = None
        if not use_remote_api:
            if mode == ResolveMode.DAILY:
                internal_target = WordleService.get_daily_word(size=size)
            elif mode == ResolveMode.RANDOM:
                internal_target = WordleService.get_random_word(
                    size=size, seed=request.seed
                )
            elif mode == ResolveMode.WORD:
                internal_target = target_word_param

        max_attempts = request.max_attempts or settings.MAX_SOLVE_ATTEMPTS
        steps: List[ResolveStep] = []
        resolved_word: Optional[str] = None
        success = False
        message = ""

        # Use async HTTP client if running against remote Votee API
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            for attempt_idx in range(1, max_attempts + 1):
                # 1. Evaluate current guess
                if use_remote_api:
                    feedback = await cls._evaluate_remote(
                        client=http_client,
                        api_url=settings.VOTEE_API_BASE_URL,
                        mode=mode,
                        guess=current_guess,
                        size=size,
                        word=target_word_param,
                        seed=request.seed,
                    )
                else:
                    assert internal_target is not None
                    feedback = WordleService.evaluate_guess(
                        target=internal_target,
                        guess=current_guess,
                    )

                # 2. Check if all slots are correct
                is_correct = all(
                    r.result == ResultKind.CORRECT for r in feedback
                )

                if is_correct:
                    success = True
                    resolved_word = current_guess
                    steps.append(
                        ResolveStep(
                            step=attempt_idx,
                            guess=current_guess,
                            results=feedback,
                            remaining_candidates_count=1,
                        )
                    )
                    message = f"Puzzle solved successfully in {attempt_idx} attempt(s)."
                    break

                # 3. Filter candidates based on feedback
                candidates = [
                    w
                    for w in candidates
                    if w != current_guess
                    and cls.matches_feedback(w, current_guess, feedback)
                ]

                remaining_count = len(candidates)
                steps.append(
                    ResolveStep(
                        step=attempt_idx,
                        guess=current_guess,
                        results=feedback,
                        remaining_candidates_count=remaining_count,
                    )
                )

                # 4. Handle candidate pool exhaustion
                if remaining_count == 0:
                    message = (
                        f"Candidate dictionary exhausted after {attempt_idx} attempts. "
                        "The target word may not exist in the local dictionary."
                    )
                    break

                # 5. Choose next guess by ranking candidates
                candidates.sort(key=cls.score_word, reverse=True)
                current_guess = candidates[0]

            if not success and not message:
                message = f"Reached maximum allowed attempts ({max_attempts}) without solving."

        return ResolveResponse(
            success=success,
            mode=mode,
            target_word=resolved_word,
            total_attempts=len(steps),
            starting_word=starting_word,
            steps=steps,
            message=message,
        )
