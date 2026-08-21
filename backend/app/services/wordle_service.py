import json
import random
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union
from app.schemas.wordle import GuessResult, ResultKind
from app.services.daily_store import DailyWordStore


class WordleService:
    _words_cache: Dict[int, List[str]] = {}
    _static_dir: Path = Path(__file__).resolve().parent.parent / "static"

    @classmethod
    def get_current_date_str(
        cls,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> str:
        """
        Get normalized date string in YYYY-MM-DD format.
        """
        return DailyWordStore._normalize_date(target_date)

    @classmethod
    def get_words_by_length(cls, size: int) -> List[str]:
        """
        Retrieve all available words of a specific character length.
        First attempts to load from static/words_by_length/words_{size}.json.
        Falls back to loading from static/words_dictionary.json if available.
        """
        if size in cls._words_cache:
            return cls._words_cache[size]

        # 1. Attempt to load partitioned JSON file
        words_length_file = cls._static_dir / "words_by_length" / f"words_{size}.json"
        if words_length_file.exists():
            with open(words_length_file, "r", encoding="utf-8") as f:
                words = json.load(f)
            cls._words_cache[size] = words
            return words

        # 2. Fallback: Parse from full words_dictionary.json
        full_dict_file = cls._static_dir / "words_dictionary.json"
        if full_dict_file.exists():
            with open(full_dict_file, "r", encoding="utf-8") as f:
                raw_dict = json.load(f)
            words = [
                word.lower()
                for word in raw_dict.keys()
                if len(word) == size and word.isalpha()
            ]
            words.sort()
            cls._words_cache[size] = words
            return words

        raise FileNotFoundError(
            f"Dictionary file for word length {size} not found at {words_length_file}"
        )

    @classmethod
    def set_daily_word(
        cls,
        word: str,
        target_date: Optional[Union[str, date, datetime]] = None,
        size: Optional[int] = None,
        save_to_disk: bool = False,
    ) -> None:
        """
        Set a static target word for a specific date in the daily store.
        """
        DailyWordStore.set_word(
            word=word,
            target_date=target_date,
            size=size,
            save_to_disk=save_to_disk,
        )

    @classmethod
    def get_daily_word(
        cls,
        size: int = 5,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> str:
        """
        Get the daily puzzle word for a given size and date.
        Checks the DailyWordStore for a preset static word first.
        If not configured, selects a deterministic word from the dictionary.
        """
        # 1. Check if a static word is configured in the store
        static_word = DailyWordStore.get_word(target_date=target_date, size=size)
        if static_word:
            return static_word

        # 2. Fallback to deterministic word selection
        words = cls.get_words_by_length(size)
        if not words:
            raise ValueError(f"No dictionary words available for length {size}")

        if target_date is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        elif isinstance(target_date, (datetime, date)):
            date_str = target_date.strftime("%Y-%m-%d")
        else:
            date_str = str(target_date).strip()

        # Seed random choice deterministically for the given date and length
        seed = f"daily-{date_str}-{size}"
        rng = random.Random(seed)
        return rng.choice(words)

    @classmethod
    def get_random_word(
        cls,
        size: int = 5,
        seed: Optional[Union[str, int]] = None,
    ) -> str:
        """
        Get a random word of a specific length.
        If a seed is provided, selection is deterministic based on that seed.
        If seed is not provided, selection is randomized.
        """
        words = cls.get_words_by_length(size)
        if not words:
            raise ValueError(f"No dictionary words available for length {size}")

        if seed is not None and str(seed).strip() != "":
            rng = random.Random(str(seed).strip())
            return rng.choice(words)

        return random.choice(words)

    @classmethod
    def evaluate_guess(cls, target: str, guess: str) -> List[GuessResult]:
        """
        Evaluate a guess against the target word according to standard Wordle rules.
        """
        target_clean = target.strip().lower()
        guess_clean = guess.strip().lower()
        n = len(guess_clean)

        results: List[Optional[ResultKind]] = [None] * n
        target_letter_counts: Dict[str, int] = {}

        # Pass 1: Identify exact matches ("correct") and count remaining target letters
        for i in range(min(n, len(target_clean))):
            if guess_clean[i] == target_clean[i]:
                results[i] = ResultKind.CORRECT
            else:
                t_char = target_clean[i]
                target_letter_counts[t_char] = target_letter_counts.get(t_char, 0) + 1

        # Pass 2: Identify "present" vs "absent" matches
        for i in range(n):
            if results[i] is not None:
                continue

            g_char = guess_clean[i]
            if target_letter_counts.get(g_char, 0) > 0:
                results[i] = ResultKind.PRESENT
                target_letter_counts[g_char] -= 1
            else:
                results[i] = ResultKind.ABSENT

        return [
            GuessResult(
                slot=i,
                guess=guess_clean[i],
                result=results[i] or ResultKind.ABSENT,
            )
            for i in range(n)
        ]
