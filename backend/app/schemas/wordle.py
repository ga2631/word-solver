from enum import Enum
from pydantic import BaseModel, Field


class ResultKind(str, Enum):
    ABSENT = "absent"
    PRESENT = "present"
    CORRECT = "correct"


class GuessResult(BaseModel):
    slot: int = Field(..., description="Index of character (0-based)")
    guess: str = Field(..., description="The character in that slot")
    result: ResultKind = Field(
        ...,
        description="Status of character in the word ('absent', 'correct', 'present')",
    )


class DailyWordInfo(BaseModel):
    date: str = Field(..., description="Date of the daily puzzle (YYYY-MM-DD)")
    size: int = Field(..., description="Word length")
    word: str = Field(..., description="The secret daily word")
