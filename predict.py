"""
Prediction module for collaborative filtering using K-Nearest Neighbors.

This module provides functions for finding nearest neighbors and predicting
ratings using weighted collaborative filtering.
"""
from typing import Tuple, Optional, List, Union, Dict, Any
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

from cluster import merge_cluster
from logger import get_logger

logger = get_logger(__name__)


def find_neighbor(
    item_id: int,
    ratings: pd.DataFrame,
    usage: str = "prediction",
    metric: str = 'correlation',
    k: int = 10,
    verbose: bool = False
) -> Union[Tuple[np.ndarray, np.ndarray], List[int]]:
    """
    Find k nearest neighbors for a given item using KNN.

    Args:
        item_id: ID of the item to find neighbors for
        ratings: DataFrame with user-item ratings (items as rows, users as columns)
        usage: Return type - 'prediction' returns similarities and indices,
               'nearest_unrated' returns list of item IDs
        metric: Distance metric for KNN ('correlation', 'cosine', 'euclidean')
        k: Number of neighbors to find
        verbose: If True, print neighbor information

    Returns:
        If usage='prediction': Tuple of (similarities, indices) arrays
        If usage='nearest_unrated': List of neighbor item IDs

    Raises:
        KeyError: If item_id not found in ratings index
        ValueError: If invalid usage parameter
    """
    # Remove cluster column if present
    ratings_clean = ratings.iloc[:, :-1] if 'cluster' in ratings.columns else ratings

    try:
        loc = ratings_clean.index.get_loc(item_id)
    except KeyError:
        logger.error(f"Item {item_id} not found in ratings data")
        raise

    # Fit KNN model
    model_knn = NearestNeighbors(metric=metric, algorithm='brute')
    model_knn.fit(ratings_clean)

    # Find k+1 neighbors (including the item itself)
    distances, indices = model_knn.kneighbors(
        ratings_clean.iloc[loc, :].values.reshape(1, -1),
        n_neighbors=k + 1
    )

    # Convert distances to similarities (1 - distance)
    similarities = 1 - distances.flatten()

    # Flatten indices once for efficiency
    indices_flat = indices.flatten()
    similarities_flat = similarities.flatten()

    if verbose:
        logger.info(f'{k} most similar items for item {item_id}:')
        for i in range(len(indices_flat)):
            if ratings_clean.index[indices_flat[i]] == item_id:
                continue
            logger.info(
                f'{i}: {ratings_clean.index[indices_flat[i]]}, '
                f'similarity: {similarities_flat[i]:.4f}'
            )

    if usage == "prediction":
        return similarities, indices
    elif usage == "nearest_unrated":
        # Return list of item IDs (excluding the query item itself)
        item_list = [
            ratings_clean.index[indices_flat[i]]
            for i in range(len(indices_flat))
        ]
        return item_list
    else:
        raise ValueError(f"Invalid usage parameter: {usage}")


def predict(
    user_id: str,
    item_id: int,
    ratings_cluster: pd.DataFrame,
    centroids: Optional[np.ndarray] = None,
    metric: str = 'correlation',
    k: int = 10,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Predict rating for a user-item pair using weighted collaborative filtering.

    Uses K-nearest neighbors to find similar items and predicts the rating
    as a weighted average of neighbor ratings, where weights are the similarities.

    Args:
        user_id: User identifier
        item_id: Item identifier to predict rating for
        ratings_cluster: DataFrame with ratings and cluster assignments
        centroids: Cluster centroids (if None, cluster merging is skipped)
        metric: Distance metric for neighbor finding
        k: Number of neighbors to use for prediction
        verbose: If True, print detailed prediction steps

    Returns:
        Dictionary with 'id' (item_id) and 'rating' (predicted rating)

    Raises:
        KeyError: If user_id or item_id not found in data
        ValueError: If insufficient neighbors found
    """
    try:
        user_loc = ratings_cluster.columns.get_loc(user_id)
    except KeyError:
        logger.error(f"User {user_id} not found in ratings data")
        raise

    try:
        # Find which cluster the item belongs to
        which_cluster = ratings_cluster.loc[
            ratings_cluster.index == item_id, 'cluster'
        ].iloc[0]

        # Get all ratings in the same cluster
        clustered_ratings = ratings_cluster.loc[
            ratings_cluster['cluster'] == which_cluster
        ]
    except (IndexError, KeyError) as e:
        logger.error(f"Item {item_id} not found in cluster data: {e}")
        raise

    # If centroids provided, check cluster size and merge if needed
    if centroids is not None:
        cluster_member = len(clustered_ratings) - 1  # Subtract the item itself
        if cluster_member < k:
            logger.debug(
                f"Cluster {which_cluster} has only {cluster_member} members, "
                f"merging with nearest cluster"
            )
            clustered_ratings = merge_cluster(
                clustered_ratings, ratings_cluster, which_cluster, centroids, k=k
            )

    # Get item location in clustered data
    item_loc = clustered_ratings.index.get_loc(item_id)

    # Find similar items
    similarities, indices = find_neighbor(
        item_id, clustered_ratings, metric=metric, k=k, usage="prediction"
    )

    # Flatten arrays once for efficiency
    indices_flat = indices.flatten()
    similarities_flat = similarities.flatten()

    # Calculate weighted prediction
    wtd_sum = 0.0
    sum_wt = 0.0

    for i in range(len(indices_flat)):
        # Skip if index is the item itself or rating is 0
        if indices_flat[i] == item_loc:
            continue

        neighbor_rating = clustered_ratings.iloc[indices_flat[i], user_loc]
        if neighbor_rating == 0:
            continue

        # Calculate weighted contribution
        similarity = similarities_flat[i]
        product = neighbor_rating * similarity

        sum_wt += abs(similarity)
        wtd_sum += product

        if verbose:
            logger.debug(
                f'{i}. item_loc: {indices_flat[i]}, user_loc: {user_loc} -> '
                f'rating: {neighbor_rating:.2f} * similarity: {similarity:.4f} = {product:.4f}'
            )

    # Calculate final prediction
    if sum_wt == 0:
        prediction = 0.0  # No similar items found
        logger.warning(f"No similar items found for item {item_id}, prediction set to 0")
    else:
        prediction = wtd_sum / sum_wt

    # Note: Rating clipping (1-5) is intentionally not applied to allow
    # filtering by threshold in the calling code

    if verbose:
        logger.info(f'Predicted rating for user {user_id} -> item {item_id}: {prediction:.4f}')

    return {"id": int(item_id), "rating": float(prediction)}
