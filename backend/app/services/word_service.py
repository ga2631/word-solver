import random
from collections import Counter
from typing import List
from app.schemas.word import (
    WordGenerateRequest,
    WordGenerateResponse,
    GeneratedWord,
    WordAnalyzeRequest,
    WordAnalyzeResponse,
)

WORD_DICTIONARY = {
    "tech": [
        "algorithm", "byte", "compiler", "database", "encryption",
        "framework", "gateway", "hardware", "interface", "javascript",
        "kernel", "lambda", "microservice", "network", "optimizer",
        "pipeline", "quantum", "runtime", "serverless", "terminal",
        "virtualization", "webhook", "zenith", "cluster", "container"
    ],
    "nature": [
        "aurora", "breeze", "cascade", "dune", "ecosystem",
        "flora", "glacier", "horizon", "island", "jungle",
        "lagoon", "meadow", "nebula", "ocean", "prairie",
        "quarry", "rainforest", "savanna", "tundra", "valley",
        "waterfall", "xenolith", "yellowwood", "zephyr", "canopy"
    ],
    "science": [
        "atom", "biology", "catalyst", "dimension", "entropy",
        "fusion", "gravity", "hypothesis", "isotope", "joule",
        "kinetics", "luminescence", "molecule", "neutron", "optics",
        "photon", "quasar", "resonance", "spectrum", "thermodynamics",
        "universe", "velocity", "wavelength", "xenon", "yield"
    ],
    "fantasy": [
        "alchemy", "behemoth", "chimera", "dragon", "enchantment",
        "fable", "griffin", "hydra", "illusion", "jinx",
        "kraken", "leviathan", "mythology", "necromancer", "oracle",
        "phoenix", "quest", "rune", "sorcery", "talisman",
        "unicorn", "valkyrie", "wizard", "wyvern", "zealot"
    ],
    "general": [
        "abstract", "beacon", "catalyst", "dynamic", "essence",
        "frontier", "glimmer", "harmony", "infinite", "journey",
        "kinetic", "legacy", "momentum", "nexus", "orbit",
        "pinnacle", "quest", "radiant", "spectrum", "triumph",
        "unity", "vibrant", "whisper", "xenial", "yield"
    ]
}


class WordService:
    @staticmethod
    def is_palindrome(word: str) -> bool:
        cleaned = word.lower().replace(" ", "")
        return cleaned == cleaned[::-1] and len(cleaned) > 1

    @classmethod
    def generate_words(cls, req: WordGenerateRequest) -> WordGenerateResponse:
        category = req.category.lower() if req.category else "general"
        pool = WORD_DICTIONARY.get(category, WORD_DICTIONARY["general"])

        # Filter by prefix and length constraints
        filtered_pool = [
            w for w in pool
            if (not req.prefix or w.lower().startswith(req.prefix.lower()))
            and req.min_length <= len(w) <= req.max_length
        ]

        if not filtered_pool:
            # Fallback to pool if filter was too restrictive
            filtered_pool = pool

        # Sample or replicate if count exceeds pool
        selected_raw: List[str] = []
        if len(filtered_pool) >= req.count:
            selected_raw = random.sample(filtered_pool, req.count)
        else:
            selected_raw = random.choices(filtered_pool, k=req.count)

        words = [
            GeneratedWord(
                word=w,
                length=len(w),
                category=category,
                is_palindrome=cls.is_palindrome(w)
            )
            for w in selected_raw
        ]

        return WordGenerateResponse(
            success=True,
            total=len(words),
            words=words
        )

    @classmethod
    def analyze_word(cls, req: WordAnalyzeRequest) -> WordAnalyzeResponse:
        word = req.word.strip()
        vowels = set("aeiouAEIOU")
        vowels_count = sum(1 for char in word if char in vowels)
        consonants_count = sum(1 for char in word if char.isalpha() and char not in vowels)
        char_freq = dict(Counter(word.lower()))

        return WordAnalyzeResponse(
            word=word,
            length=len(word),
            vowels_count=vowels_count,
            consonants_count=consonants_count,
            is_palindrome=cls.is_palindrome(word),
            reversed=word[::-1],
            character_frequencies=char_freq
        )
