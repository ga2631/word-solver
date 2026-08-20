from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.word import (
    WordGenerateRequest,
    WordGenerateResponse,
    WordAnalyzeRequest,
    WordAnalyzeResponse,
)
from app.services.word_service import WordService, WORD_DICTIONARY

router = APIRouter()


@router.get("/categories", response_model=List[str], summary="Get Available Categories")
async def get_categories() -> List[str]:
    """
    Return the list of supported word categories.
    """
    return list(WORD_DICTIONARY.keys())


@router.get("/generate", response_model=WordGenerateResponse, summary="Generate Words via Query Params")
async def generate_words_get(
    category: str = Query("general", description="Category of words (e.g. tech, nature, science, fantasy, general)"),
    count: int = Query(5, ge=1, le=50, description="Number of words to generate"),
    prefix: Optional[str] = Query("", max_length=10, description="Prefix to filter words"),
    min_length: int = Query(3, ge=1, le=30, description="Minimum length"),
    max_length: int = Query(15, ge=1, le=30, description="Maximum length"),
) -> WordGenerateResponse:
    """
    Generate random words based on query filters.
    """
    if min_length > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_length cannot be greater than max_length",
        )

    req = WordGenerateRequest(
        category=category,
        count=count,
        prefix=prefix,
        min_length=min_length,
        max_length=max_length,
    )
    return WordService.generate_words(req)


@router.post("/generate", response_model=WordGenerateResponse, summary="Generate Words via JSON Payload")
async def generate_words_post(req: WordGenerateRequest) -> WordGenerateResponse:
    """
    Generate random words based on request body payload.
    """
    if req.min_length and req.max_length and req.min_length > req.max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_length cannot be greater than max_length",
        )
    return WordService.generate_words(req)


@router.post("/analyze", response_model=WordAnalyzeResponse, summary="Analyze Word Characteristics")
async def analyze_word(req: WordAnalyzeRequest) -> WordAnalyzeResponse:
    """
    Analyze word properties (length, vowels, consonants, palindrome check, char frequencies).
    """
    return WordService.analyze_word(req)
