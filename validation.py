"""
Input validation and schema checking for Kappa Backend API.
"""
from typing import Dict, List, Any, Optional
from config import Config


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_user_input(user_input: Any) -> List[Dict[str, Any]]:
    """
    Validate user input for recommendation endpoints.

    Args:
        user_input: User input data (expected to be a list of rating dictionaries)

    Returns:
        Validated user input

    Raises:
        ValidationError: If input is invalid
    """
    # Check if input is present
    if user_input is None:
        raise ValidationError("Request body is required")

    # Check if input is a list
    if not isinstance(user_input, list):
        raise ValidationError("Input must be a list of ratings")

    # Check minimum number of ratings
    if len(user_input) < Config.MIN_USER_RATINGS:
        raise ValidationError(
            f"At least {Config.MIN_USER_RATINGS} ratings are required, got {len(user_input)}"
        )

    # Check maximum number of ratings
    if len(user_input) > Config.MAX_USER_RATINGS:
        raise ValidationError(
            f"Maximum {Config.MAX_USER_RATINGS} ratings allowed, got {len(user_input)}"
        )

    # Validate each rating
    for idx, rating in enumerate(user_input):
        if not isinstance(rating, dict):
            raise ValidationError(f"Rating at index {idx} must be a dictionary")

        # Check required fields
        required_fields = ['id', 'rating']
        for field in required_fields:
            if field not in rating:
                raise ValidationError(f"Rating at index {idx} missing required field: {field}")

        # Validate id
        comic_id = rating.get('id')
        if not isinstance(comic_id, (int, float)):
            raise ValidationError(f"Rating at index {idx}: 'id' must be a number, got {type(comic_id).__name__}")

        # Validate rating value
        rating_value = rating.get('rating')
        if not isinstance(rating_value, (int, float)):
            raise ValidationError(
                f"Rating at index {idx}: 'rating' must be a number, got {type(rating_value).__name__}"
            )

        if not (Config.MIN_RATING_VALUE <= rating_value <= Config.MAX_RATING_VALUE):
            raise ValidationError(
                f"Rating at index {idx}: 'rating' must be between {Config.MIN_RATING_VALUE} "
                f"and {Config.MAX_RATING_VALUE}, got {rating_value}"
            )

    return user_input


def validate_algorithm_params(algorithm: str, **kwargs) -> Dict[str, Any]:
    """
    Validate algorithm-specific parameters.

    Args:
        algorithm: Algorithm name ('kmeans' or 'dbscan')
        **kwargs: Algorithm parameters

    Returns:
        Validated parameters

    Raises:
        ValidationError: If parameters are invalid
    """
    if algorithm not in ['kmeans', 'dbscan']:
        raise ValidationError(f"Unknown algorithm: {algorithm}")

    validated = {}

    if algorithm == 'kmeans':
        n_clusters = kwargs.get('n_clusters', Config.KMEANS_CLUSTERS)
        if not isinstance(n_clusters, int) or n_clusters < 1:
            raise ValidationError(f"n_clusters must be a positive integer, got {n_clusters}")
        validated['n_clusters'] = n_clusters

    elif algorithm == 'dbscan':
        epsilon = kwargs.get('epsilon', Config.DBSCAN_EPSILON)
        if not isinstance(epsilon, (int, float)) or epsilon <= 0:
            raise ValidationError(f"epsilon must be a positive number, got {epsilon}")
        validated['epsilon'] = epsilon

    return validated
