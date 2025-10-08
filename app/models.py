"""
Pydantic models for request and response schemas
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


# Request Models

class ParseRequest(BaseModel):
    """Request model for single text parsing"""
    text: str = Field(..., description="Text to parse", min_length=1)
    language: str = Field("portuguese", description="Language code (e.g., 'portuguese', 'english')")
    mwe_enabled: bool = Field(True, description="Enable MWE recognition")

    class Config:
        schema_extra = {
            "example": {
                "text": "Tomei café da manhã antes de sair.",
                "language": "portuguese",
                "mwe_enabled": True
            }
        }


class BatchParseRequest(BaseModel):
    """Request model for batch text parsing"""
    texts: List[str] = Field(..., description="List of texts to parse", min_items=1)
    language: str = Field("portuguese", description="Language code")
    mwe_enabled: bool = Field(True, description="Enable MWE recognition")

    class Config:
        schema_extra = {
            "example": {
                "texts": [
                    "Tomei café da manhã.",
                    "De acordo com o relatório, tudo está correto."
                ],
                "language": "portuguese",
                "mwe_enabled": True
            }
        }


class MWEOnlyRequest(BaseModel):
    """Request model for MWE-only recognition (lightweight)"""
    text: str = Field(..., description="Text to analyze for MWEs", min_length=1)
    language: str = Field("portuguese", description="Language code")

    class Config:
        schema_extra = {
            "example": {
                "text": "Tomei café da manhã de acordo com o plano.",
                "language": "portuguese"
            }
        }


class TokensRequest(BaseModel):
    """Request model for parsing pre-tokenized text"""
    tokens: List[str] = Field(..., description="List of tokens", min_items=1)
    language: str = Field("portuguese", description="Language code")
    mwe_enabled: bool = Field(True, description="Enable MWE recognition")

    class Config:
        schema_extra = {
            "example": {
                "tokens": ["Tomei", "café", "da", "manhã", "."],
                "language": "portuguese",
                "mwe_enabled": True
            }
        }


# Response Models

class MWEAnnotation(BaseModel):
    """MWE annotation details"""
    span: Tuple[int, int] = Field(..., description="Token span (start, end)")
    text: str = Field(..., description="Surface form of the MWE")
    lemma: str = Field(..., description="Lemma form of the MWE")
    pos: str = Field(..., description="Part-of-speech tag")
    type: str = Field(..., description="MWE type (fixed, flat, compound)")
    tokens: List[str] = Field(..., description="List of tokens in the MWE")


class ParseResponse(BaseModel):
    """Response model for parsing requests"""
    sentences: List[Dict[str, Any]] = Field(..., description="Parsed sentences with full annotations")
    mwe_count: int = Field(..., description="Total number of MWEs detected")
    mwes: List[MWEAnnotation] = Field(default_factory=list, description="List of detected MWEs")
    language: str = Field(..., description="Language used for parsing")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class BatchParseResponse(BaseModel):
    """Response model for batch parsing"""
    results: List[ParseResponse] = Field(..., description="List of parse results")
    total_texts: int = Field(..., description="Total number of texts processed")
    total_mwes: int = Field(..., description="Total MWEs detected across all texts")
    total_processing_time: Optional[float] = Field(None, description="Total processing time in seconds")


class MWEOnlyResponse(BaseModel):
    """Response model for MWE-only requests"""
    text: str = Field(..., description="Original text")
    mwe_count: int = Field(..., description="Number of MWEs detected")
    mwes: List[MWEAnnotation] = Field(..., description="List of detected MWEs")
    language: str = Field(..., description="Language used")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    models_loaded: List[str] = Field(..., description="List of loaded language models")
    mwe_enabled: bool = Field(..., description="Whether MWE recognition is enabled")
    mwe_database_size: Optional[int] = Field(None, description="Number of MWEs in database")
    lemma_dict_size: Optional[int] = Field(None, description="Number of lemma mappings")


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")
