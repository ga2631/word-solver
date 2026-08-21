from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
import httpx
from app.schemas.resolve import (
    ResolveMode,
    ResolveRequest,
    ResolveResponse,
)
from app.services.resolver_service import ResolverService

router = APIRouter()

@router.get(
    "/resolve",
    response_model=ResolveResponse,
    summary="Resolve Wordle Puzzle (GET)",
    description="Convenience GET endpoint to resolve a Wordle puzzle with query parameters.",
)
async def resolve_puzzle_get(
    mode: ResolveMode = Query(
        ResolveMode.DAILY,
        description="Target game mode: 'daily', 'random', or 'word'",
    ),
    size: int = Query(
        5,
        ge=1,
        le=50,
        description="Word length (default: 5)",
    ),
    word: Optional[str] = Query(
        None,
        description="Target word (required when mode is 'word')",
    ),
    seed: Optional[str] = Query(
        None,
        description="Optional seed string for random mode",
    ),
    starting_word: Optional[str] = Query(
        None,
        description="Custom initial starting word",
    ),
    max_attempts: int = Query(
        30,
        ge=1,
        le=100,
        description="Max guess attempts allowed",
    ),
) -> ResolveResponse:
    request = ResolveRequest(
        mode=mode,
        size=size,
        word=word,
        seed=seed,
        starting_word=starting_word,
        max_attempts=max_attempts,
    )
    try:
        return await ResolverService.resolve(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External API communication error: {str(e)}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
