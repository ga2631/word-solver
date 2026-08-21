from typing import List
from fastapi import APIRouter, HTTPException, Query, Response, status
from app.core.config import settings
from app.schemas.wordle import GuessResult
from app.services.wordle_service import WordleService

router = APIRouter()


@router.get(
    "/daily",
    response_model=List[GuessResult],
    summary="Guess Daily Word",
    description="Check your guess against the daily puzzle word.",
)
async def guess_daily(
    response: Response,
    guess: str = Query(..., description="The guess word"),
    size: int = Query(5, ge=1, le=50, description="Length of word (default: 5)"),
) -> List[GuessResult]:
    clean_guess = guess.strip()
    if len(clean_guess) != size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Length of guess '{guess}' ({len(clean_guess)}) does not match size ({size})",
        )

    try:
        target_word = WordleService.get_daily_word(size=size)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No dictionary available for word length {size}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # When test flag is enabled, expose daily target word via response headers
    if settings.SHOW_DAILY_WORD or settings.TEST_MODE:
        response.headers["X-Daily-Word"] = target_word
        response.headers["X-Target-Word"] = target_word

    return WordleService.evaluate_guess(target=target_word, guess=clean_guess)