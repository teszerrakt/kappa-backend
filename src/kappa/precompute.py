import numpy as np
import pandas as pd

from kappa.cluster import kmeans_clustering, dbscan_clustering
from kappa.database import fetch_comic_genre_df, fetch_ratings_df, save_precomputed
from kappa.load_data import load_rating_data


def run_precompute(method):
    ratings_df = fetch_ratings_df()
    comic_genre_df = fetch_comic_genre_df()
    if ratings_df.empty or comic_genre_df.empty:
        raise ValueError("Missing ratings or comic genre data")

    user_item_matrix, cluster_data = load_rating_data(comic_genre_df, ratings_df)

    if method == "kmeans":
        ratings_cluster, centroids = kmeans_clustering(
            2, cluster_data, user_item_matrix
        )
        cluster_labels = ratings_cluster["cluster"].values
    elif method == "dbscan":
        ratings_cluster = dbscan_clustering(7.8, cluster_data, user_item_matrix)
        centroids = None
        cluster_labels = ratings_cluster["cluster"].values
    else:
        raise ValueError("Unknown precompute method")

    save_precomputed(method, user_item_matrix, cluster_labels, centroids)
    return {
        "method": method,
        "items": int(len(user_item_matrix.index)),
    }


def build_ratings_cluster(user_item_matrix, cluster_labels):
    ratings_cluster = pd.concat(
        [
            user_item_matrix.reset_index(),
            pd.DataFrame({"cluster": np.array(cluster_labels)}),
        ],
        axis=1,
    )
    return ratings_cluster.set_index("comicID")
