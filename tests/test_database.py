import sqlite3

from kappa.database import (
    fetch_comic_genre_df,
    fetch_comics_by_ids,
    fetch_ratings_df,
    list_comics,
    load_precomputed,
    save_precomputed,
    upsert_comic_genres,
    upsert_comics,
)


def test_init_db_creates_tables(db_tables):
    assert "ratings" in db_tables
    assert "comics" in db_tables
    assert "comic_genres" in db_tables
    assert "precomputed_matrices" in db_tables


def test_insert_ratings_fetches_rows(ratings_df):
    assert len(ratings_df) > 0
    assert set(ratings_df.columns) == {"username", "comicID", "rating"}


def test_upsert_comics_updates_title(sample_comics):
    upsert_comics(sample_comics)
    updated = [{"comic_id": 1, "title": "Alpha Updated", "image_url": "https://img/1"}]
    upsert_comics(updated)
    result = fetch_comics_by_ids([1])
    assert result[1]["title"] == "Alpha Updated"


def test_fetch_comics_by_ids_empty():
    assert fetch_comics_by_ids([]) == {}


def test_list_comics_pagination(sample_comics):
    upsert_comics(sample_comics)
    page = list_comics(limit=2, offset=1)
    assert len(page) == 2
    assert page[0]["id"] == 2


def test_upsert_comic_genres_updates(sample_genres):
    upsert_comic_genres(sample_genres)
    updated = [{**sample_genres[0], "Action": 0, "Drama": 1}]
    upsert_comic_genres(updated)
    genres_df = fetch_comic_genre_df()
    row = genres_df.loc[genres_df["comicID"] == 1].iloc[0]
    assert int(row["Action"]) == 0
    assert int(row["Drama"]) == 1


def test_save_and_load_precomputed_round_trip(ratings_df, genres_df):
    import pandas as pd
    import numpy as np

    user_item = ratings_df.pivot_table(
        index="comicID",
        columns="username",
        values="rating",
        fill_value=0,
        aggfunc="max",
    )
    cluster_labels = np.zeros(len(user_item.index))
    save_precomputed(
        "kmeans", user_item, cluster_labels, centroids=np.array([[0.0, 1.0]])
    )
    loaded = load_precomputed("kmeans")
    assert loaded is not None
    assert isinstance(loaded["user_item_matrix"], pd.DataFrame)
    assert len(loaded["cluster_labels"]) == len(user_item.index)


def test_load_precomputed_missing():
    assert load_precomputed("missing") is None
