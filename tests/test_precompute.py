import pytest

from kappa.precompute import build_ratings_cluster, run_precompute


def test_run_precompute_kmeans(seeded_db):
    result = run_precompute("kmeans")
    assert result["method"] == "kmeans"
    assert result["items"] > 0


def test_run_precompute_dbscan(seeded_db):
    result = run_precompute("dbscan")
    assert result["method"] == "dbscan"
    assert result["items"] > 0


def test_run_precompute_unknown_method(seeded_db):
    with pytest.raises(ValueError):
        run_precompute("unknown")


def test_build_ratings_cluster(ratings_df, genres_df):
    user_item_matrix = ratings_df.pivot_table(
        index="comicID",
        columns="username",
        values="rating",
        fill_value=0,
        aggfunc="max",
    )
    cluster_labels = [0 for _ in range(len(user_item_matrix.index))]
    ratings_cluster = build_ratings_cluster(user_item_matrix, cluster_labels)
    assert "cluster" in ratings_cluster.columns
    assert ratings_cluster.index.name == "comicID"
