import os
import pickle
import sqlite3
from datetime import datetime, timezone

import pandas as pd

GENRE_COLUMNS = [
    "Action",
    "Adventure",
    "Cars",
    "Comedy",
    "Dementia",
    "Demons",
    "Doujinshi",
    "Drama",
    "Ecchi",
    "Fantasy",
    "Game",
    "GenderBender",
    "Harem",
    "Hentai",
    "Historical",
    "Horror",
    "Josei",
    "Kids",
    "Magic",
    "MartialArts",
    "Mecha",
    "Military",
    "Music",
    "Mystery",
    "Parody",
    "Police",
    "Psychological",
    "Romance",
    "Samurai",
    "School",
    "Sci-Fi",
    "Seinen",
    "Shoujo",
    "ShoujoAi",
    "Shounen",
    "ShounenAi",
    "SliceofLife",
    "Space",
    "Sports",
    "SuperPower",
    "Supernatural",
    "Thriller",
    "Vampire",
    "Yaoi",
    "Yuri",
    "Unknown",
]


def _quote_identifier(name):
    return '"{}"'.format(name.replace('"', '""'))


def get_db_path():
    return os.environ.get("KAPPA_DB_PATH", "kappa.db")


def get_connection():
    return sqlite3.connect(get_db_path())


def init_db():
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            comic_id INTEGER NOT NULL,
            rating REAL NOT NULL,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comic_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            image_url TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    genre_columns_sql = ",\n            ".join(
        ["comic_id INTEGER NOT NULL UNIQUE"]
        + [
            "{} INTEGER NOT NULL DEFAULT 0".format(_quote_identifier(col))
            for col in GENRE_COLUMNS
        ]
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comic_genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {}
        )
        """.format(genre_columns_sql)
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS precomputed_matrices (
            method TEXT PRIMARY KEY,
            user_item_matrix BLOB,
            cluster_labels BLOB,
            centroids BLOB,
            computed_at TEXT
        )
        """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_ratings_comic_id ON ratings(comic_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_ratings_username ON ratings(username)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comics_comic_id ON comics(comic_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_comic_genres_comic_id ON comic_genres(comic_id)"
    )

    conn.commit()
    conn.close()


def fetch_ratings_df():
    conn = get_connection()
    ratings_df = pd.read_sql_query(
        "SELECT username, comic_id AS comicID, rating FROM ratings",
        conn,
    )
    conn.close()
    return ratings_df


def fetch_comic_genre_df():
    conn = get_connection()
    genre_columns = ", ".join(
        ["comic_id AS comicID"] + [_quote_identifier(col) for col in GENRE_COLUMNS]
    )
    genre_df = pd.read_sql_query(
        "SELECT {} FROM comic_genres".format(genre_columns),
        conn,
    )
    conn.close()
    return genre_df


def fetch_comics_by_ids(comic_ids):
    if not comic_ids:
        return {}
    placeholders = ",".join(["?"] * len(comic_ids))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT comic_id, title, image_url FROM comics WHERE comic_id IN ({})".format(
            placeholders
        ),
        comic_ids,
    )
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {"title": row[1], "image_url": row[2]} for row in rows}


def list_comics(limit=50, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT comic_id, title, image_url FROM comics ORDER BY comic_id LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "image_url": row[2]} for row in rows]


def upsert_comics(comics):
    if not comics:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    values = []
    for comic in comics:
        values.append(
            (
                comic["comic_id"],
                comic.get("title"),
                comic.get("image_url"),
                now,
                now,
            )
        )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO comics (comic_id, title, image_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(comic_id) DO UPDATE SET
            title=excluded.title,
            image_url=excluded.image_url,
            updated_at=excluded.updated_at
        """,
        values,
    )
    conn.commit()
    conn.close()
    return len(values)


def upsert_comic_genres(genres):
    if not genres:
        return 0
    columns = ["comic_id"] + GENRE_COLUMNS
    placeholders = ",".join(["?"] * len(columns))
    values = []
    for genre in genres:
        row = [genre["comic_id"]]
        for col in GENRE_COLUMNS:
            raw_value = genre.get(col, 0)
            row.append(int(raw_value) if raw_value is not None else 0)
        values.append(tuple(row))
    conn = get_connection()
    cursor = conn.cursor()
    quoted_columns = ["comic_id"] + [_quote_identifier(col) for col in GENRE_COLUMNS]
    update_clause = ", ".join(
        ["{0}=excluded.{0}".format(_quote_identifier(col)) for col in GENRE_COLUMNS]
    )
    cursor.executemany(
        """
        INSERT INTO comic_genres ({columns})
        VALUES ({placeholders})
        ON CONFLICT(comic_id) DO UPDATE SET {updates}
        """.format(
            columns=", ".join(quoted_columns),
            placeholders=placeholders,
            updates=update_clause,
        ),
        values,
    )
    conn.commit()
    conn.close()
    return len(values)


def insert_ratings(ratings):
    if not ratings:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    values = []
    for rating in ratings:
        values.append(
            (
                rating["username"],
                rating["comic_id"],
                float(rating["rating"]),
                now,
            )
        )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO ratings (username, comic_id, rating, created_at)
        VALUES (?, ?, ?, ?)
        """,
        values,
    )
    conn.commit()
    conn.close()
    return len(values)


def save_precomputed(method, user_item_matrix, cluster_labels, centroids):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO precomputed_matrices (method, user_item_matrix, cluster_labels, centroids, computed_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(method) DO UPDATE SET
            user_item_matrix=excluded.user_item_matrix,
            cluster_labels=excluded.cluster_labels,
            centroids=excluded.centroids,
            computed_at=excluded.computed_at
        """,
        (
            method,
            sqlite3.Binary(
                pickle.dumps(user_item_matrix, protocol=pickle.HIGHEST_PROTOCOL)
            ),
            sqlite3.Binary(
                pickle.dumps(cluster_labels, protocol=pickle.HIGHEST_PROTOCOL)
            ),
            sqlite3.Binary(pickle.dumps(centroids, protocol=pickle.HIGHEST_PROTOCOL)),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def load_precomputed(method):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_item_matrix, cluster_labels, centroids, computed_at FROM precomputed_matrices WHERE method = ?",
        (method,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_item_matrix": pickle.loads(row[0]),
        "cluster_labels": pickle.loads(row[1]),
        "centroids": pickle.loads(row[2]),
        "computed_at": row[3],
    }
