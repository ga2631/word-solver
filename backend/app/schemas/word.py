from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HealthCheck(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WordGenerateRequest(BaseModel):
    category: Optional[str] = Field(default="general", description="Category: general, tech, nature, science, fantasy")
    count: int = Field(default=5, ge=1, le=50, description="Number of words to generate")
    prefix: Optional[str] = Field(default="", max_length=10, description="Optional prefix for words")
    min_length: Optional[int] = Field(default=3, ge=1, le=30, description="Minimum word length")
    max_length: Optional[int] = Field(default=15, ge=1, le=30, description="Maximum word length")


class GeneratedWord(BaseModel):
    word: str
    length: int
    category: str
    is_palindrome: bool


class WordGenerateResponse(BaseModel):
    success: bool = True
    total: int
    words: List[GeneratedWord]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class WordAnalyzeRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)


class WordAnalyzeResponse(BaseModel):
    word: str
    length: int
    vowels_count: int
    consonants_count: int
    is_palindrome: bool
    reversed: str
    character_frequencies: dict[str, int]
