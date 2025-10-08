"""
Trankit MWE API - FastAPI application with MWE recognition support
"""

import time
from typing import Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from trankit import Pipeline

from .config import settings
from .models import (
    ParseRequest, BatchParseRequest, MWEOnlyRequest, TokensRequest,
    ParseResponse, BatchParseResponse, MWEOnlyResponse, HealthResponse,
    MWEAnnotation, ErrorResponse
)

# Print configuration on startup
settings.print_config()

# Initialize FastAPI app
app = FastAPI(
    title="Trankit MWE API",
    description="Natural Language Processing API with Multiword Expression (MWE) recognition",
    version=settings.VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipelines: Dict[str, Pipeline] = {}


def initialize_pipeline(language: str) -> Pipeline:
    """
    Initialize or retrieve cached pipeline for a language.

    Args:
        language: Language code

    Returns:
        Pipeline instance
    """
    if language not in pipelines:
        print(f"Initializing pipeline for language: {language}")

        mwe_config = settings.get_mwe_config() if settings.MWE_ENABLED else {}

        pipeline = Pipeline(
            lang=language,
            cache_dir=settings.CACHE_DIR,
            gpu=settings.GPU_ENABLED,
            embedding=settings.EMBEDDING_MODEL,
            **mwe_config
        )

        pipelines[language] = pipeline
        print(f"✓ Pipeline initialized for {language}")

    return pipelines[language]


def extract_mwe_annotations(result: dict) -> list:
    """
    Extract MWE annotations from parsing result.

    Args:
        result: Parsing result from pipeline

    Returns:
        List of MWE annotations
    """
    mwes = []

    for sentence in result.get('sentences', []):
        tokens = sentence.get('tokens', [])

        # Track which tokens are part of MWEs
        seen_spans = set()

        for token in tokens:
            if 'mwe_span' in token:
                span = token['mwe_span']
                span_key = (span[0], span[1])

                # Only add each MWE once (not for every token in the span)
                if span_key not in seen_spans:
                    seen_spans.add(span_key)

                    # Get all tokens in this MWE span
                    mwe_tokens = [
                        t['text'] for t in tokens
                        if 'mwe_span' in t and t['mwe_span'] == span
                    ]

                    mwes.append(MWEAnnotation(
                        span=span,
                        text=' '.join(mwe_tokens),
                        lemma=token.get('mwe_lemma', ''),
                        pos=token.get('mwe_pos', ''),
                        type=token.get('mwe_type', ''),
                        tokens=mwe_tokens
                    ))

    return mwes


@app.on_event("startup")
async def startup_event():
    """Initialize default pipeline on startup"""
    print("Starting Trankit MWE API...")
    print(f"Initializing default pipeline for {settings.DEFAULT_LANGUAGE}...")
    initialize_pipeline(settings.DEFAULT_LANGUAGE)
    print("✓ API ready to accept requests")


@app.get(
    f"{settings.API_PREFIX}/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"]
)
async def health_check():
    """Check API health and loaded models"""
    mwe_database_size = None
    lemma_dict_size = None

    # Get MWE statistics from default language pipeline
    if settings.DEFAULT_LANGUAGE in pipelines:
        pipeline = pipelines[settings.DEFAULT_LANGUAGE]
        mwe_recognizer = pipeline._mwe_recognizer.get(settings.DEFAULT_LANGUAGE)
        if mwe_recognizer:
            mwe_database_size = len(mwe_recognizer.mwe_database)
            lemma_dict_size = len(mwe_recognizer.lemma_dict)

    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        models_loaded=list(pipelines.keys()),
        mwe_enabled=settings.MWE_ENABLED,
        mwe_database_size=mwe_database_size,
        lemma_dict_size=lemma_dict_size
    )


@app.post(
    f"{settings.API_PREFIX}/parse",
    response_model=ParseResponse,
    summary="Parse text with full NLP pipeline",
    tags=["Parsing"]
)
async def parse_text(request: ParseRequest):
    """
    Parse text with full NLP pipeline including MWE recognition.

    Returns detailed linguistic annotations including:
    - Sentence segmentation
    - Tokenization
    - POS tagging
    - Morphological features
    - Dependency parsing
    - Lemmatization
    - MWE recognition (if enabled)
    """
    try:
        start_time = time.time()

        # Initialize pipeline for language
        pipeline = initialize_pipeline(request.language)

        # Parse text
        result = pipeline(request.text)

        # Extract MWE annotations
        mwes = extract_mwe_annotations(result) if request.mwe_enabled else []

        processing_time = time.time() - start_time

        return ParseResponse(
            sentences=result['sentences'],
            mwe_count=len(mwes),
            mwes=mwes,
            language=request.language,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing text: {str(e)}"
        )


@app.post(
    f"{settings.API_PREFIX}/parse_batch",
    response_model=BatchParseResponse,
    summary="Parse multiple texts in batch",
    tags=["Parsing"]
)
async def parse_batch(request: BatchParseRequest):
    """
    Parse multiple texts in batch.

    Processes multiple texts with the same language and settings.
    More efficient than making individual requests.
    """
    try:
        start_time = time.time()

        # Initialize pipeline
        pipeline = initialize_pipeline(request.language)

        # Process all texts
        results = []
        total_mwes = 0

        for text in request.texts:
            result = pipeline(text)
            mwes = extract_mwe_annotations(result) if request.mwe_enabled else []
            total_mwes += len(mwes)

            results.append(ParseResponse(
                sentences=result['sentences'],
                mwe_count=len(mwes),
                mwes=mwes,
                language=request.language,
                processing_time=None  # Individual times not tracked in batch
            ))

        total_processing_time = time.time() - start_time

        return BatchParseResponse(
            results=results,
            total_texts=len(request.texts),
            total_mwes=total_mwes,
            total_processing_time=total_processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing batch: {str(e)}"
        )


@app.post(
    f"{settings.API_PREFIX}/mwe_only",
    response_model=MWEOnlyResponse,
    summary="MWE recognition only (lightweight)",
    tags=["MWE"]
)
async def mwe_only(request: MWEOnlyRequest):
    """
    Perform only MWE recognition without full parsing.

    Lighter and faster than full parsing - returns only MWE annotations.
    Useful when you only need to identify multiword expressions.
    """
    try:
        start_time = time.time()

        if not settings.MWE_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MWE recognition is not enabled on this server"
            )

        # Initialize pipeline
        pipeline = initialize_pipeline(request.language)

        # Parse text (MWE recognition happens during parsing)
        result = pipeline(request.text)

        # Extract only MWE annotations
        mwes = extract_mwe_annotations(result)

        processing_time = time.time() - start_time

        return MWEOnlyResponse(
            text=request.text,
            mwe_count=len(mwes),
            mwes=mwes,
            language=request.language,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recognizing MWEs: {str(e)}"
        )


@app.post(
    f"{settings.API_PREFIX}/parse_tokens",
    response_model=ParseResponse,
    summary="Parse pre-tokenized text",
    tags=["Parsing"]
)
async def parse_tokens(request: TokensRequest):
    """
    Parse pre-tokenized text.

    Use this endpoint when you already have tokenized text.
    Useful for integration with other NLP pipelines.
    """
    try:
        start_time = time.time()

        # Initialize pipeline
        pipeline = initialize_pipeline(request.language)

        # Parse pre-tokenized text
        result = pipeline.posdep(request.tokens, is_sent=True)

        # Extract MWE annotations
        mwes = extract_mwe_annotations(result) if request.mwe_enabled else []

        processing_time = time.time() - start_time

        return ParseResponse(
            sentences=[result] if not isinstance(result, list) else result,
            mwe_count=len(mwes),
            mwes=mwes,
            language=request.language,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing tokens: {str(e)}"
        )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=None,
            status_code=exc.status_code
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ).dict()
    )


# Root redirect
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation"""
    return {
        "message": "Trankit MWE API",
        "version": settings.VERSION,
        "docs": f"{settings.API_PREFIX}/docs",
        "health": f"{settings.API_PREFIX}/health"
    }
