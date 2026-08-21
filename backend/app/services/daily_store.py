import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


class DailyWordStore:
    """
    In-memory and file-backed store for static Wordle puzzle words by date.
    Allows configuring specific target words for particular dates and sizes.
    """

    _store: Dict[str, Dict[int, str]] = {}
    _default_file: Path = (
        Path(__file__).resolve().parent.parent / "static" / "daily_words.json"
    )
    _initialized: bool = False

    @classmethod
    def _normalize_date(cls, target_date: Optional[Union[str, date, datetime]] = None) -> str:
        """
        Normalize date input into standard 'YYYY-MM-DD' string format.
        """
        if target_date is None:
            return datetime.utcnow().strftime("%Y-%m-%d")
        if isinstance(target_date, (datetime, date)):
            return target_date.strftime("%Y-%m-%d")
        return str(target_date).strip()

    @classmethod
    def load_store(cls, file_path: Optional[Path] = None) -> None:
        """
        Load static daily words from a JSON file into memory.
        Supports both nested: {"2026-08-21": {"5": "crane"}}
        and flat: {"2026-08-21": "crane"} formats.
        """
        target_path = file_path or cls._default_file
        if not target_path.exists():
            cls._initialized = True
            return

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            cls._store.clear()
            for raw_date, entry in data.items():
                date_key = cls._normalize_date(raw_date)
                if isinstance(entry, dict):
                    cls._store[date_key] = {}
                    for size_key, word in entry.items():
                        try:
                            s = int(size_key)
                            cls._store[date_key][s] = str(word).strip().lower()
                        except ValueError:
                            continue
                elif isinstance(entry, str):
                    w = entry.strip().lower()
                    cls._store[date_key] = {len(w): w}

            cls._initialized = True
            logger.info(f"Loaded {len(cls._store)} daily word entries from {target_path}")
        except Exception as e:
            logger.error(f"Failed to load daily words store from {target_path}: {e}")
            cls._initialized = True

    @classmethod
    def save_store(cls, file_path: Optional[Path] = None) -> None:
        """
        Save the current in-memory store to a JSON file.
        """
        target_path = file_path or cls._default_file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert integer size keys to strings for JSON serialization
        serializable_data = {
            date_key: {str(s): word for s, word in size_map.items()}
            for date_key, size_map in cls._store.items()
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_word(
        cls,
        target_date: Optional[Union[str, date, datetime]] = None,
        size: int = 5,
    ) -> Optional[str]:
        """
        Retrieve a static word for the given date and size if preset.
        """
        if not cls._initialized:
            cls.load_store()

        date_str = cls._normalize_date(target_date)
        date_entries = cls._store.get(date_str)
        if date_entries and size in date_entries:
            return date_entries[size]
        return None

    @classmethod
    def set_word(
        cls,
        word: str,
        target_date: Optional[Union[str, date, datetime]] = None,
        size: Optional[int] = None,
        save_to_disk: bool = False,
    ) -> None:
        """
        Set or override the static word for a given date and size.
        """
        if not cls._initialized:
            cls.load_store()

        date_str = cls._normalize_date(target_date)
        clean_word = word.strip().lower()
        word_size = size if size is not None else len(clean_word)

        if date_str not in cls._store:
            cls._store[date_str] = {}

        cls._store[date_str][word_size] = clean_word

        if save_to_disk:
            cls.save_store()

    @classmethod
    def has_word(
        cls,
        target_date: Optional[Union[str, date, datetime]] = None,
        size: int = 5,
    ) -> bool:
        """
        Check if a static word is set for the specified date and size.
        """
        return cls.get_word(target_date=target_date, size=size) is not None

    @classmethod
    def clear_store(cls) -> None:
        """
        Clear in-memory store (primarily for unit tests).
        """
        cls._store.clear()
        cls._initialized = True

    @classmethod
    def get_all_stored_words(cls) -> Dict[str, Dict[int, str]]:
        """
        Return a copy of the entire in-memory store.
        """
        if not cls._initialized:
            cls.load_store()
        return {k: dict(v) for k, v in cls._store.items()}
