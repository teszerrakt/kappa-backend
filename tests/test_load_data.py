import pandas as pd

from kappa.load_data import load_rating_data, merge_user_rating


def test_merge_user_rating_adds_username(ratings_df):
    user_input = [{"id": 42, "rating": 5, "title": "Test"}]
    combined = merge_user_rating(user_input, ratings_df)
    assert "username" in combined.columns
    assert "comicID" in combined.columns
    assert combined.iloc[0]["username"] == "KAPPA_NEW_USER"


def test_load_rating_data_pivot_and_merge(genres_df, ratings_df):
    user_item_matrix, cluster_data = load_rating_data(genres_df, ratings_df)
    assert isinstance(user_item_matrix, pd.DataFrame)
    assert "cluster" not in user_item_matrix.columns
    assert "Action" in cluster_data.columns
    assert user_item_matrix.index.name == "comicID"


def test_load_rating_data_inner_join_filters_missing(genres_df, ratings_df):
    extra = ratings_df.copy()
    extra = pd.concat(
        [extra, pd.DataFrame([{"username": "test", "comicID": 999, "rating": 3.0}])],
        ignore_index=True,
    )
    user_item_matrix, cluster_data = load_rating_data(genres_df, extra)
    assert 999 not in cluster_data.index
