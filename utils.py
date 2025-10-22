"""
Utility functions for Kappa Backend API.
"""
from typing import List, Dict, Any, Optional, Tuple
import timeit
import pandas as pd
import numpy as np
from config import Config
from logger import get_logger

logger = get_logger(__name__)


def find_nearest_unrated(
    user_input: List[Dict[str, Any]],
    ratings_cluster: pd.DataFrame,
    find_neighbor_func: callable
) -> np.ndarray:
    """
    Find nearest unrated items for a user based on their rated items.

    Args:
        user_input: List of user ratings with 'id' and 'rating' keys
        ratings_cluster: DataFrame with ratings and cluster assignments
        find_neighbor_func: Function to find neighbors (from predict module)

    Returns:
        Array of item IDs to predict ratings for
    """
    rated_comics = np.array([user_input[i]['id'] for i in range(len(user_input))])
    item_to_predict = []

    for item in rated_comics:
        try:
            which_cluster = ratings_cluster.loc[
                ratings_cluster.index == item, 'cluster'
            ].iloc[0]
            clustered_ratings = ratings_cluster.loc[
                ratings_cluster['cluster'] == which_cluster
            ]

            neighbors = find_neighbor_func(
                item, clustered_ratings, usage="nearest_unrated", verbose=False
            )
            item_to_predict.append(neighbors)
        except (IndexError, KeyError) as e:
            logger.warning(f"Item {item} not found in cluster data: {e}")
            continue

    # Convert to 1D array, remove duplicates and rated comics
    item_to_predict = np.array(item_to_predict).flatten()
    item_to_predict = np.unique(item_to_predict)
    item_to_predict = np.setdiff1d(item_to_predict, rated_comics)

    return item_to_predict


def enrich_prediction_with_metadata(
    prediction: Dict[str, Any],
    comic_data: pd.DataFrame
) -> Optional[Dict[str, Any]]:
    """
    Enrich prediction with comic metadata (title and image URL).

    Args:
        prediction: Prediction dictionary with 'id' and 'rating' keys
        comic_data: DataFrame with comic metadata

    Returns:
        Enriched prediction dictionary or None if metadata not found
    """
    comic_id = prediction['id']

    try:
        comic_row = comic_data.loc[comic_data['comic_id'] == comic_id]
        if comic_row.empty:
            logger.warning(f"Comic metadata not found for ID: {comic_id}")
            return None

        prediction['title'] = comic_row.iat[0, 1]
        prediction['image_url'] = comic_row.iat[0, 2]
        return prediction
    except (IndexError, KeyError) as e:
        logger.error(f"Error enriching prediction for comic {comic_id}: {e}")
        return None


def filter_and_sort_predictions(
    predictions: List[Dict[str, Any]],
    min_rating: float = None
) -> List[Dict[str, Any]]:
    """
    Filter predictions by minimum rating and sort by rating descending.

    Args:
        predictions: List of prediction dictionaries
        min_rating: Minimum rating threshold (defaults to Config.MIN_RATING_THRESHOLD)

    Returns:
        Filtered and sorted predictions
    """
    if min_rating is None:
        min_rating = Config.MIN_RATING_THRESHOLD

    # Filter by minimum rating
    filtered = [p for p in predictions if p['rating'] >= min_rating]

    # Sort by rating descending
    sorted_predictions = sorted(filtered, key=lambda x: x['rating'], reverse=True)

    return sorted_predictions


def load_csv_data(
    rating_file: str,
    genre_file: str,
    comic_file: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all required CSV data files.

    Args:
        rating_file: Path to rating data CSV
        genre_file: Path to genre data CSV
        comic_file: Path to comic metadata CSV

    Returns:
        Tuple of (rating_data, genre_data, comic_data) DataFrames

    Raises:
        FileNotFoundError: If any file is not found
        pd.errors.ParserError: If CSV parsing fails
    """
    logger.info("Loading data files...")

    try:
        all_data = pd.read_csv(rating_file)
        logger.info(f"Loaded rating data: {len(all_data)} records")

        comic_genre = pd.read_csv(genre_file)
        logger.info(f"Loaded genre data: {len(comic_genre)} records")

        comic_data = pd.read_csv(comic_file)
        logger.info(f"Loaded comic metadata: {len(comic_data)} records")

        return all_data, comic_genre, comic_data

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing CSV file: {e}")
        raise


class Timer:
    """Simple context manager for timing operations."""

    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = timeit.default_timer()
        return self

    def __exit__(self, *args):
        self.elapsed = timeit.default_timer() - self.start_time
        logger.info(f"{self.operation_name} completed in {self.elapsed:.2f} seconds")
