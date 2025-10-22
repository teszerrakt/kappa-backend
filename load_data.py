"""
Data loading and preparation utilities for comic recommendation system.

This module handles merging user input with historical rating data and
preparing data matrices for clustering and prediction.
"""
from typing import List, Dict, Any, Tuple
import pandas as pd

from logger import get_logger

logger = get_logger(__name__)


def merge_user_rating(
    user_rating: List[Dict[str, Any]],
    all_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge user rating input with historical rating data.

    Args:
        user_rating: List of user rating dictionaries with keys:
                    - 'id': Comic ID
                    - 'rating': User rating (1-5)
                    - 'title': Comic title (optional, will be dropped)
        all_data: DataFrame with historical rating data containing columns:
                 - 'comicID': Comic identifier
                 - 'username': User identifier
                 - 'rating': Rating value

    Returns:
        Combined DataFrame with user ratings and historical data

    Raises:
        ValueError: If user_rating is empty or has invalid structure
        KeyError: If required columns are missing
    """
    if not user_rating:
        raise ValueError("user_rating cannot be empty")

    logger.debug(f"Merging {len(user_rating)} user ratings with historical data")

    # Create dummy username for new user
    username = ['KAPPA_NEW_USER'] * len(user_rating)
    username_df = pd.DataFrame({'username': username})

    # Create DataFrame from user rating
    user_prefs = pd.DataFrame(user_rating)

    # Drop title column if present (not needed for clustering)
    if 'title' in user_prefs.columns:
        user_prefs = user_prefs.drop(columns='title')

    # Rename 'id' to 'comicID' to match historical data schema
    if 'id' in user_prefs.columns:
        user_prefs = user_prefs.rename(columns={'id': 'comicID'})
    else:
        raise KeyError("'id' column not found in user_rating")

    # Add username to user preferences
    user_prefs = pd.concat([user_prefs, username_df], axis=1)

    # Validate required columns
    required_columns = ['comicID', 'rating', 'username']
    for col in required_columns:
        if col not in user_prefs.columns:
            raise KeyError(f"Required column '{col}' not found in user preferences")

    # Merge with historical data
    combined = pd.concat([user_prefs, all_data], axis=0, ignore_index=True)

    logger.debug(f"Data merged successfully: {len(combined)} total records")

    return combined


def load_rating_data(
    comic_genre: pd.DataFrame,
    rating_data: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare user-item matrix and feature-enhanced cluster dataset.

    Creates two matrices:
    1. User-item matrix: Items as rows, users as columns, ratings as values
    2. Cluster dataset: User-item matrix enhanced with genre features

    Args:
        comic_genre: DataFrame with genre features for each comic
                    Must have 'comicID' as a column
        rating_data: DataFrame with rating data containing:
                    - 'comicID': Comic identifier
                    - 'username': User identifier
                    - 'rating': Rating value

    Returns:
        Tuple of:
            - user_item_matrix: Pivot table with comicID as index,
                              username as columns, rating as values
            - cluster_dataset: user_item_matrix merged with genre features
                             (excludes comicID column)

    Raises:
        KeyError: If required columns are missing
        ValueError: If merge fails due to no common comics
    """
    logger.debug("Creating user-item matrix")

    # Validate required columns
    required_rating_cols = ['comicID', 'username', 'rating']
    for col in required_rating_cols:
        if col not in rating_data.columns:
            raise KeyError(f"Required column '{col}' not found in rating_data")

    if 'comicID' not in comic_genre.columns:
        raise KeyError("'comicID' column not found in comic_genre")

    # Create user-item matrix
    # - Index: comicID
    # - Columns: username
    # - Values: rating (0 for missing ratings)
    # - aggfunc='max': If duplicate entries, take maximum rating
    user_item_matrix = rating_data.pivot_table(
        index='comicID',
        columns='username',
        values='rating',
        fill_value=0,
        aggfunc='max'
    )

    logger.debug(
        f"User-item matrix created: {len(user_item_matrix)} items, "
        f"{len(user_item_matrix.columns)} users"
    )

    # Create cluster dataset by merging with genre features
    cluster_dataset = user_item_matrix.copy()
    cluster_dataset = pd.merge(
        cluster_dataset,
        comic_genre,
        on='comicID',
        how='left'
    )

    # Count comics with missing genre data
    missing_genres = cluster_dataset.isnull().any(axis=1).sum()
    if missing_genres > 0:
        logger.warning(
            f"{missing_genres} comics missing genre data "
            "(will have NaN values in features)"
        )

    # Fill NaN values with 0 for clustering algorithms
    cluster_dataset = cluster_dataset.fillna(0)

    # Remove comicID column (first column) as it's now the index
    # Keep only user ratings and genre features
    cluster_features = cluster_dataset.iloc[:, 1:]

    logger.debug(
        f"Cluster dataset prepared: {len(cluster_features)} items, "
        f"{len(cluster_features.columns)} features"
    )

    return user_item_matrix, cluster_features
