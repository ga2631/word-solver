from typing import List
from fastapi import APIRouter, HTTPException, Path, Query, Response, status
from app.core.config import settings
from app.schemas.wordle import GuessResult
from app.services.wordle_service import WordleService

router = APIRouter()


@router.get(
    "/word/{word}",
    response_model=List[GuessResult],
    summary="Guess Word",
    description="Check your guess against a specified puzzle word.",
)
async def guess_word(
    response: Response,
    word: str = Path(..., description="The target word to guess against"),
    guess: str = Query(..., description="The guess word"),
) -> List[GuessResult]:
    clean_target = word.strip()
    clean_guess = guess.strip()

    if len(clean_guess) != len(clean_target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Length of guess '{guess}' ({len(clean_guess)}) "
                f"does not match target word '{word}' ({len(clean_target)})"
            ),
        )

    # When test mode is enabled, expose target word in response headers
    if settings.TEST_MODE:
        response.headers["X-Target-Word"] = clean_target

    return WordleService.evaluate_guess(target=clean_target, guess=clean_guess)
