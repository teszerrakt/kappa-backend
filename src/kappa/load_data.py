import pandas as pd


def merge_user_rating(user_rating, all_data):
    # Create dummy username
    username = ["KAPPA_NEW_USER" for i in range(len(user_rating))]
    username = pd.DataFrame(username)
    username.columns = ["username"]

    # Cleaning user rating data
    user_prefs = pd.DataFrame(user_rating)  # Create a dataframe from user_rating
    user_prefs = user_prefs.drop(columns="title")  # Removing title columns
    user_prefs = user_prefs.rename(
        columns={"id": "comicID"}
    )  # Renaming "id" with "comicID" to match with the .csv data

    # Add username data into user_prefs
    user_prefs = pd.concat([user_prefs, username], axis=1)

    # Merging with all of the data
    combined = pd.concat([user_prefs, all_data], axis=0)

    return combined


def load_rating_data(comic_genre, rating_data):
    user_item_matrix = rating_data.pivot_table(
        index="comicID",
        columns="username",
        values="rating",
        fill_value=0,
        aggfunc="max",
    )

    cluster_dataset = user_item_matrix.copy()
    cluster_dataset = pd.merge(cluster_dataset, comic_genre, on="comicID", how="inner")

    return user_item_matrix, cluster_dataset.iloc[:, 1:]
