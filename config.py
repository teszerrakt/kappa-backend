"""
Configuration management for Kappa Backend API.
"""
import os
from typing import Optional


class Config:
    """Application configuration with environment variable support."""

    # Flask Configuration
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '80'))

    # Data File Paths
    DATA_DIR: str = os.getenv('DATA_DIR', '/home/user/kappa-backend')
    RATING_FILE: str = os.getenv('RATING_FILE', 'rating_5_min_75.csv')
    GENRE_FILE: str = os.getenv('GENRE_FILE', 'comic_genre.csv')
    COMIC_FILE: str = os.getenv('COMIC_FILE', 'firestore_comics.csv')

    # Algorithm Hyperparameters
    KMEANS_CLUSTERS: int = int(os.getenv('KMEANS_CLUSTERS', '2'))
    DBSCAN_EPSILON: float = float(os.getenv('DBSCAN_EPSILON', '7.8'))
    KNN_K: int = int(os.getenv('KNN_K', '10'))
    MIN_RATING_THRESHOLD: float = float(os.getenv('MIN_RATING_THRESHOLD', '3.0'))

    # Validation
    MIN_USER_RATINGS: int = int(os.getenv('MIN_USER_RATINGS', '5'))
    MAX_USER_RATINGS: int = int(os.getenv('MAX_USER_RATINGS', '1000'))
    MIN_RATING_VALUE: float = 1.0
    MAX_RATING_VALUE: float = 5.0

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # CORS
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_DEFAULT: str = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')

    @classmethod
    def get_file_path(cls, filename: str) -> str:
        """Get full path for a data file."""
        return os.path.join(cls.DATA_DIR, filename)

    @classmethod
    def validate(cls) -> None:
        """Validate configuration and check if required files exist."""
        required_files = [
            cls.get_file_path(cls.RATING_FILE),
            cls.get_file_path(cls.GENRE_FILE),
            cls.get_file_path(cls.COMIC_FILE),
        ]

        for filepath in required_files:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Required data file not found: {filepath}")

        # Validate hyperparameters
        if cls.KMEANS_CLUSTERS < 1:
            raise ValueError("KMEANS_CLUSTERS must be >= 1")

        if cls.DBSCAN_EPSILON <= 0:
            raise ValueError("DBSCAN_EPSILON must be > 0")

        if cls.KNN_K < 1:
            raise ValueError("KNN_K must be >= 1")

        if not (0 <= cls.MIN_RATING_THRESHOLD <= 5):
            raise ValueError("MIN_RATING_THRESHOLD must be between 0 and 5")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    RATE_LIMIT_DEFAULT = '50 per hour'


class TestConfig(Config):
    """Test configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


# Configuration factory
def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration based on environment.

    Args:
        env: Environment name ('development', 'production', 'test')

    Returns:
        Configuration object
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'production')

    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'test': TestConfig,
    }

    return configs.get(env.lower(), ProductionConfig)()
