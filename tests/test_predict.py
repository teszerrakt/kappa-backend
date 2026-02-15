import numpy as np

from kappa.cluster import kmeans_clustering
from kappa.predict import find_neighbor, predict


def _build_ratings_cluster(ratings_df, genres_df):
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
    return ratings_cluster, centroids


def test_find_neighbor_nearest_unrated(ratings_df, genres_df):
    ratings_cluster, _ = _build_ratings_cluster(ratings_df, genres_df)
    item_id = ratings_cluster.index[0]
    items = find_neighbor(item_id, ratings_cluster, usage="nearest_unrated", k=3)
    assert isinstance(items, list)
    assert len(items) > 0


def test_find_neighbor_prediction_returns_arrays(ratings_df, genres_df):
    ratings_cluster, _ = _build_ratings_cluster(ratings_df, genres_df)
    item_id = ratings_cluster.index[0]
    similarities, indices = find_neighbor(
        item_id, ratings_cluster, usage="prediction", k=3
    )
    assert isinstance(similarities, np.ndarray)
    assert isinstance(indices, np.ndarray)


def test_predict_returns_dict(ratings_df, genres_df):
    ratings_cluster, centroids = _build_ratings_cluster(ratings_df, genres_df)
    item_id = ratings_cluster.index[0]
    result = predict("alice", item_id, ratings_cluster, centroids, k=3)
    assert "id" in result
    assert "rating" in result


def test_predict_zero_sum_similarity(ratings_df, genres_df):
    ratings_cluster, centroids = _build_ratings_cluster(ratings_df, genres_df)
    ratings_cluster.loc[:, :] = 0
    item_id = ratings_cluster.index[0]
    result = predict("alice", item_id, ratings_cluster, centroids, k=3)
    assert result["rating"] == 0
