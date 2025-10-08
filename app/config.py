"""
Configuration management for Trankit MWE API
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""

    # Project settings
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "trankit-mwe")
    VERSION: str = "1.0.0"
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "80"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))

    # GPU settings
    GPU_ENABLED: bool = os.getenv("GPU_ENABLED", "false").lower() in ("true", "1", "yes")

    # Language settings
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "portuguese")
    SUPPORTED_LANGUAGES: list = os.getenv(
        "SUPPORTED_LANGUAGES",
        "portuguese,english"
    ).split(",")

    # MWE settings
    MWE_DATABASE_PATH: str = os.getenv(
        "MWE_DATABASE_PATH",
        "data/portuguese/mwe_database.json"
    )
    LEMMA_DICT_PATH: str = os.getenv(
        "LEMMA_DICT_PATH",
        "data/portuguese/lemma_dict.json"
    )
    MWE_ENABLED: bool = os.getenv("MWE_ENABLED", "true").lower() in ("true", "1", "yes")

    # Cache settings
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./cache/trankit/")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "xlm-roberta-base")

    # CORS settings
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "*"
    ).split(",")

    # Timeout settings (seconds)
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "300"))
    GRACEFUL_TIMEOUT: int = int(os.getenv("GRACEFUL_TIMEOUT", "600"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    @classmethod
    def validate(cls) -> None:
        """Validate configuration settings"""
        # Check if MWE files exist if MWE is enabled
        if cls.MWE_ENABLED:
            mwe_path = Path(cls.MWE_DATABASE_PATH)
            if not mwe_path.exists():
                print(f"Warning: MWE database not found at {cls.MWE_DATABASE_PATH}")
                print("MWE recognition will be disabled. Run extraction script first:")
                print("  python scripts/extract_dictionaries_from_db.py")
                cls.MWE_ENABLED = False

            lemma_path = Path(cls.LEMMA_DICT_PATH)
            if not lemma_path.exists():
                print(f"Warning: Lemma dictionary not found at {cls.LEMMA_DICT_PATH}")
                print("Using without lemma dictionary (may reduce accuracy)")

        # Ensure cache directory exists
        Path(cls.CACHE_DIR).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_mwe_config(cls) -> Optional[dict]:
        """Get MWE configuration for pipeline initialization"""
        if not cls.MWE_ENABLED:
            return None

        config = {}

        # Check if files exist
        if Path(cls.MWE_DATABASE_PATH).exists():
            config['mwe_database'] = cls.MWE_DATABASE_PATH

        if Path(cls.LEMMA_DICT_PATH).exists():
            config['lemma_dict'] = cls.LEMMA_DICT_PATH

        return config if config else None

    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (for debugging)"""
        print("=" * 80)
        print("Trankit MWE API Configuration")
        print("=" * 80)
        print(f"Project: {cls.PROJECT_NAME} v{cls.VERSION}")
        print(f"API Prefix: {cls.API_PREFIX}")
        print(f"Host: {cls.HOST}:{cls.PORT}")
        print(f"Workers: {cls.WORKERS}")
        print(f"GPU Enabled: {cls.GPU_ENABLED}")
        print(f"Default Language: {cls.DEFAULT_LANGUAGE}")
        print(f"Supported Languages: {', '.join(cls.SUPPORTED_LANGUAGES)}")
        print(f"MWE Enabled: {cls.MWE_ENABLED}")
        if cls.MWE_ENABLED:
            print(f"MWE Database: {cls.MWE_DATABASE_PATH}")
            print(f"Lemma Dict: {cls.LEMMA_DICT_PATH}")
        print(f"Cache Directory: {cls.CACHE_DIR}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("=" * 80)


# Initialize and validate settings on import
settings = Settings()
settings.validate()
