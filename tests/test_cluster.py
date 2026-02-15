import numpy as np

from kappa.cluster import (
    dbscan_clustering,
    find_centroid_distance,
    kmeans_clustering,
    merge_cluster,
)


def test_kmeans_clustering_returns_cluster_column(ratings_df, genres_df):
    user_item_matrix = ratings_df.pivot_table(
        index="comicID",
        columns="username",
        values="rating",
        fill_value=0,
        aggfunc="max",
    )
    cluster_data = user_item_matrix.merge(genres_df, on="comicID", how="inner").iloc[
        :, 1:
    ]
    ratings_cluster, centroids = kmeans_clustering(2, cluster_data, user_item_matrix)
    assert "cluster" in ratings_cluster.columns
    assert centroids.shape[0] == 2


def test_dbscan_clustering_returns_cluster_column(ratings_df, genres_df):
    user_item_matrix = ratings_df.pivot_table(
        index="comicID",
        columns="username",
        values="rating",
        fill_value=0,
        aggfunc="max",
    )
    cluster_data = user_item_matrix.merge(genres_df, on="comicID", how="inner").iloc[
        :, 1:
    ]
    ratings_cluster = dbscan_clustering(7.8, cluster_data, user_item_matrix)
    assert "cluster" in ratings_cluster.columns


def test_find_centroid_distance_returns_other_clusters():
    centroids = np.array([[0.0, 0.0], [1.0, 1.0]])
    distances = find_centroid_distance(0, centroids)
    assert 1 in distances
    assert distances[1] > 0


def test_merge_cluster_increases_members(ratings_df, genres_df):
    user_item_matrix = ratings_df.pivot_table(
        index="comicID",
        columns="username",
        values="rating",
        fill_value=0,
        aggfunc="max",
    )
    cluster_data = user_item_matrix.merge(genres_df, on="comicID", how="inner").iloc[
        :, 1:
    ]
    ratings_cluster, centroids = kmeans_clustering(2, cluster_data, user_item_matrix)
    first_cluster = ratings_cluster[ratings_cluster["cluster"] == 0]
    merged = merge_cluster(first_cluster, ratings_cluster, 0, centroids, k=10)
    assert len(merged) >= len(first_cluster)
