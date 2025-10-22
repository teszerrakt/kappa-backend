"""
Clustering algorithms for comic recommendation system.

This module provides K-Means and DBSCAN clustering implementations,
along with utilities for cluster merging and centroid distance calculation.
"""
from typing import Tuple, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import euclidean_distances as dist

from logger import get_logger

logger = get_logger(__name__)


def kmeans_clustering(
    n_clusters: int,
    cluster_data: pd.DataFrame,
    rating_data: pd.DataFrame
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Perform K-Means clustering on rating data.

    Args:
        n_clusters: Number of clusters to create
        cluster_data: Feature matrix for clustering (ratings + genre features)
        rating_data: User-item rating matrix

    Returns:
        Tuple of:
            - ratings_cluster: Rating DataFrame with cluster assignments
            - centroids: Cluster centroid coordinates

    Raises:
        ValueError: If n_clusters < 1 or incompatible data dimensions
    """
    if n_clusters < 1:
        raise ValueError(f"n_clusters must be >= 1, got {n_clusters}")

    logger.info(f"Performing K-Means clustering with {n_clusters} clusters")

    # Perform K-Means clustering
    kmeans = KMeans(
        n_clusters=n_clusters,
        init='k-means++',
        random_state=1337,
        n_init=10
    )
    kmeans.fit(cluster_data)

    centroids = kmeans.cluster_centers_
    cluster_prediction = kmeans.predict(cluster_data)

    # Add cluster assignments to rating data
    ratings_cluster = pd.concat([
        rating_data.reset_index(),
        pd.DataFrame({'cluster': cluster_prediction})
    ], axis=1)

    # Re-set comicID as index
    ratings_cluster = ratings_cluster.set_index('comicID')

    logger.info(f"K-Means clustering completed: {n_clusters} clusters created")

    return ratings_cluster, centroids


def dbscan_clustering(
    epsilon: float,
    cluster_data: pd.DataFrame,
    rating_data: pd.DataFrame,
    min_pts: int = 11,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Perform DBSCAN (Density-Based Spatial Clustering) on rating data.

    Args:
        epsilon: Maximum distance between two samples for one to be
                considered in the neighborhood of the other
        cluster_data: Feature matrix for clustering (ratings + genre features)
        rating_data: User-item rating matrix
        min_pts: Minimum number of samples in a neighborhood for a point
                to be considered a core point
        verbose: If True, print cluster statistics

    Returns:
        Rating DataFrame with cluster assignments (includes noise cluster -1)

    Raises:
        ValueError: If epsilon <= 0 or min_pts < 1
    """
    if epsilon <= 0:
        raise ValueError(f"epsilon must be > 0, got {epsilon}")

    if min_pts < 1:
        raise ValueError(f"min_pts must be >= 1, got {min_pts}")

    logger.info(f"Performing DBSCAN clustering with epsilon={epsilon}, min_pts={min_pts}")

    # Perform DBSCAN clustering
    dbscan = DBSCAN(eps=epsilon, min_samples=min_pts)
    cluster_prediction = dbscan.fit_predict(cluster_data)

    # Add cluster assignments to rating data
    ratings_cluster = pd.concat([
        rating_data.reset_index(),
        pd.DataFrame({'cluster': cluster_prediction})
    ], axis=1)

    # Re-set comicID as index
    ratings_cluster = ratings_cluster.set_index('comicID')

    # Log cluster statistics
    cluster_labels = set(cluster_prediction)
    n_clusters = len(cluster_labels) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_prediction).count(-1)

    logger.info(
        f"DBSCAN clustering completed: {n_clusters} clusters, "
        f"{n_noise} noise points"
    )

    if verbose:
        logger.info(f"Total unique clusters: {len(cluster_labels)}")
        for c in cluster_labels:
            cluster_size = len(ratings_cluster.loc[ratings_cluster['cluster'] == c])
            cluster_type = "Noise" if c == -1 else f"Cluster {c}"
            logger.info(f"{cluster_type}: {cluster_size} items")

    return ratings_cluster


def find_centroid_distance(
    which_cluster: int,
    centroids: np.ndarray,
    verbose: bool = False
) -> Dict[int, float]:
    """
    Calculate Euclidean distances from a cluster to all other clusters.

    Args:
        which_cluster: Index of the cluster to calculate distances from
        centroids: Array of cluster centroid coordinates
        verbose: If True, print distance information

    Returns:
        Dictionary mapping cluster indices to distances

    Raises:
        IndexError: If which_cluster is out of bounds
        ValueError: If centroids array is invalid
    """
    if which_cluster < 0 or which_cluster >= len(centroids):
        raise IndexError(
            f"which_cluster {which_cluster} out of bounds for {len(centroids)} clusters"
        )

    centroid_distance = {}

    for i in range(len(centroids)):
        if i == which_cluster:
            continue

        distance = dist(
            centroids[which_cluster].reshape(1, -1),
            centroids[i].reshape(1, -1)
        )
        centroid_distance[i] = distance[0][0]

        if verbose:
            logger.debug(
                f"Distance from cluster {which_cluster} to cluster {i}: "
                f"{centroid_distance[i]:.4f}"
            )

    return centroid_distance


def merge_cluster(
    clustered_ratings: pd.DataFrame,
    all_ratings: pd.DataFrame,
    which_cluster: int,
    centroids: np.ndarray,
    k: int = 10
) -> pd.DataFrame:
    """
    Merge a cluster with its nearest neighbor clusters until sufficient members.

    This function is used when a cluster has insufficient members for the
    k-nearest neighbors algorithm. It iteratively merges the cluster with
    its nearest neighbors until it has at least k members.

    Args:
        clustered_ratings: DataFrame with ratings from the current cluster
        all_ratings: DataFrame with all ratings and cluster assignments
        which_cluster: Index of the cluster to merge
        centroids: Array of cluster centroid coordinates
        k: Minimum number of members required

    Returns:
        Extended DataFrame with merged cluster ratings

    Raises:
        ValueError: If insufficient clusters to merge
    """
    cluster_member = len(clustered_ratings) - 1  # Subtract the query item

    logger.debug(
        f"Merging cluster {which_cluster} (current size: {cluster_member}, "
        f"required: {k})"
    )

    # Find distances to other clusters
    cluster_distance = find_centroid_distance(which_cluster, centroids)

    if not cluster_distance:
        logger.warning(
            f"No other clusters available to merge with cluster {which_cluster}"
        )
        return clustered_ratings

    # Sort clusters by distance and merge iteratively
    sorted_clusters = sorted(cluster_distance.items(), key=lambda x: x[1])

    for nearest_cluster_id, distance in sorted_clusters:
        if cluster_member >= k:
            break

        logger.debug(
            f"Merging cluster {which_cluster} with cluster {nearest_cluster_id} "
            f"(distance: {distance:.4f})"
        )

        # Get ratings from nearest cluster
        nearest_cluster = all_ratings.loc[
            all_ratings['cluster'] == nearest_cluster_id
        ]

        # Merge with current cluster
        clustered_ratings = pd.concat([clustered_ratings, nearest_cluster], axis=0)
        cluster_member = len(clustered_ratings) - 1

    logger.debug(
        f"Cluster merging completed: final size {cluster_member}"
    )

    return clustered_ratings
