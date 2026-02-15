import pandas as pd

from kappa.database import (
    GENRE_COLUMNS,
    init_db,
    insert_ratings,
    upsert_comic_genres,
    upsert_comics,
)


def load_ratings_from_csv(path):
    ratings_df = pd.read_csv(path)
    ratings = []
    for _, row in ratings_df.iterrows():
        ratings.append(
            {
                "username": row["username"],
                "comic_id": int(row["comicID"]),
                "rating": float(row["rating"]),
            }
        )
    return ratings


def load_comic_genres_from_csv(path):
    genre_df = pd.read_csv(path)
    genres = []
    for _, row in genre_df.iterrows():
        entry = {"comic_id": int(row["comicID"])}
        for col in GENRE_COLUMNS:
            entry[col] = int(row.get(col, 0))
        genres.append(entry)
    return genres


def load_comics_from_csv(path):
    comics_df = pd.read_csv(path)
    comics_df.columns = [col.strip() for col in comics_df.columns]
    comics = []
    for _, row in comics_df.iterrows():
        comics.append(
            {
                "comic_id": int(row["comic_id"]),
                "title": row.get("title"),
                "image_url": row.get("image_url"),
            }
        )
    return comics


def main():
    init_db()
    ratings = load_ratings_from_csv("rating_5_min_75.csv")
    genres = load_comic_genres_from_csv("comic_genre.csv")
    comics = load_comics_from_csv("firestore_comics.csv")

    inserted_ratings = insert_ratings(ratings)
    upserted_genres = upsert_comic_genres(genres)
    upserted_comics = upsert_comics(comics)

    print("Imported ratings:", inserted_ratings)
    print("Imported comic genres:", upserted_genres)
    print("Imported comics:", upserted_comics)


if __name__ == "__main__":
    main()
