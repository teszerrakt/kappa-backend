import os
import sys
from datetime import datetime, timezone

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from kappa.database import (
    GENRE_COLUMNS,
    fetch_comic_genre_df,
    fetch_ratings_df,
    get_connection,
    init_db,
    insert_ratings,
    upsert_comic_genres,
    upsert_comics,
)


@pytest.fixture(autouse=True)
def reset_db_env(tmp_path, monkeypatch):
    db_path = tmp_path / "kappa_test.db"
    monkeypatch.setenv("KAPPA_DB_PATH", str(db_path))
    init_db()
    yield


@pytest.fixture()
def sample_comics():
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "comic_id": 1,
            "title": "Alpha",
            "image_url": "https://img/1",
            "created_at": now,
        },
        {
            "comic_id": 2,
            "title": "Beta",
            "image_url": "https://img/2",
            "created_at": now,
        },
        {
            "comic_id": 3,
            "title": "Gamma",
            "image_url": "https://img/3",
            "created_at": now,
        },
        {
            "comic_id": 4,
            "title": "Delta",
            "image_url": "https://img/4",
            "created_at": now,
        },
        {
            "comic_id": 5,
            "title": "Epsilon",
            "image_url": "https://img/5",
            "created_at": now,
        },
    ]


@pytest.fixture()
def sample_genres():
    genres = []
    for comic_id in range(1, 6):
        entry = {"comic_id": comic_id}
        for col in GENRE_COLUMNS:
            entry[col] = 0
        entry["Action"] = 1 if comic_id % 2 == 0 else 0
        entry["Drama"] = 1 if comic_id % 3 == 0 else 0
        genres.append(entry)
    return genres


@pytest.fixture()
def sample_ratings():
    ratings = []
    for username in ["alice", "bob", "carl"]:
        for comic_id in range(1, 6):
            ratings.append(
                {
                    "username": username,
                    "comic_id": comic_id,
                    "rating": float((comic_id % 5) + 1),
                }
            )
    return ratings


@pytest.fixture()
def seeded_db(sample_comics, sample_genres, sample_ratings):
    upsert_comics(sample_comics)
    upsert_comic_genres(sample_genres)
    insert_ratings(sample_ratings)
    return {
        "comics": sample_comics,
        "genres": sample_genres,
        "ratings": sample_ratings,
    }


@pytest.fixture()
def app_client(monkeypatch, seeded_db):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    main._invalidate_precomputed_cache()
    client = main.app.test_client()
    return client


@pytest.fixture()
def precomputed_client(monkeypatch, seeded_db):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    main._invalidate_precomputed_cache()
    response = main.app.test_client().post(
        "/api/precompute", headers={"X-API-Key": "test-token"}
    )
    assert response.status_code == 200
    return main.app.test_client()


@pytest.fixture()
def db_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    return tables


@pytest.fixture()
def ratings_df(seeded_db):
    return fetch_ratings_df()


@pytest.fixture()
def genres_df(seeded_db):
    return fetch_comic_genre_df()
