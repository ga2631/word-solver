from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.wordle import GuessResult


class ResolveMode(str, Enum):
    DAILY = "daily"
    RANDOM = "random"
    WORD = "word"


class ResolveRequest(BaseModel):
    mode: ResolveMode = Field(
        default=ResolveMode.DAILY,
        description="Target game mode: 'daily', 'random', or 'word'",
    )
    size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Length of the word to resolve (default: 5)",
    )
    word: Optional[str] = Field(
        default=None,
        description="Target word (required when mode is 'word')",
    )
    seed: Optional[str] = Field(
        default=None,
        description="Optional seed string for deterministic random mode",
    )
    starting_word: Optional[str] = Field(
        default=None,
        description="Custom initial starting word (default: 'crane' or best letter-frequency candidate)",
    )
    max_attempts: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Maximum guess attempts allowed before terminating",
    )


class ResolveStep(BaseModel):
    step: int = Field(..., description="1-indexed step/attempt number")
    guess: str = Field(..., description="The word guessed in this attempt")
    results: List[GuessResult] = Field(
        ...,
        description="Evaluator feedback per slot ('correct', 'present', 'absent')",
    )
    remaining_candidates_count: int = Field(
        ...,
        description="Number of remaining valid candidates after applying feedback",
    )


class ResolveResponse(BaseModel):
    success: bool = Field(
        ...,
        description="Whether the puzzle was successfully solved",
    )
    mode: ResolveMode = Field(
        ...,
        description="Puzzle mode ('daily', 'random', 'word')",
    )
    target_word: Optional[str] = Field(
        default=None,
        description="The resolved target word",
    )
    total_attempts: int = Field(
        ...,
        description="Total guess attempts taken",
    )
    starting_word: str = Field(
        ...,
        description="The initial word guessed",
    )
    steps: List[ResolveStep] = Field(
        ...,
        description="Sequence of steps taken to solve the puzzle",
    )
    message: str = Field(
        ...,
        description="Result summary or error message",
    )
