from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.wordle import GuessResult


class StartingWordResponse(BaseModel):
    size: int = Field(..., description="Word character length")
    starting_word: str = Field(..., description="Strategic initial starting word")
    total_candidates: int = Field(..., description="Total candidate words for this size")


class HistoryStepInput(BaseModel):
    guess: str = Field(..., description="The word guessed in this step")
    feedback: List[GuessResult] = Field(..., description="Feedback slots for the guess")


class NextGuessRequest(BaseModel):
    size: int = Field(..., ge=1, le=50, description="Word character length")
    history: List[HistoryStepInput] = Field(
        ..., description="List of previous guess attempts and their feedbacks"
    )


class NextGuessResponse(BaseModel):
    next_guess: Optional[str] = Field(
        None, description="Recommended next guess word with highest information score"
    )
    remaining_candidates_count: int = Field(
        ..., description="Number of candidate words remaining"
    )
    eliminated_letters: List[str] = Field(
        default_factory=list, description="Alphabet letters confirmed absent"
    )
    is_exhausted: bool = Field(
        False, description="True if no remaining candidates match feedback"
    )
    execution_time_ms: float = Field(
        0.0, description="Execution time in milliseconds"
    )
