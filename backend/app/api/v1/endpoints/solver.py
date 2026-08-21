from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.solver import (
    NextGuessRequest,
    NextGuessResponse,
    StartingWordResponse,
)
from app.services.resolver_service import ResolverService
from app.services.wordle_service import WordleService

router = APIRouter()


@router.get(
    "/starting-word",
    response_model=StartingWordResponse,
    summary="Get Strategic Starting Word",
    description="Retrieve the optimal starting word for a specific word length according to information theory.",
)
async def get_starting_word(
    size: int = Query(
        5,
        ge=1,
        le=50,
        description="Word character length (default: 5)",
    ),
) -> StartingWordResponse:
    try:
        candidates = WordleService.get_words_by_length(size)
        starting_word = ResolverService.get_starting_word(size)
        return StartingWordResponse(
            size=size,
            starting_word=starting_word,
            total_candidates=len(candidates),
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/next-guess",
    response_model=NextGuessResponse,
    summary="Calculate Next Optimal Guess",
    description="Calculates the next optimal guess word and remaining candidate count based on previous attempt feedbacks.",
)
async def calculate_next_guess(
    request: NextGuessRequest,
) -> NextGuessResponse:
    try:
        return ResolverService.get_next_guess(
            size=request.size,
            history=request.history,
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
