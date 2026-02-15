# KAPPA BACKEND
import os
import threading
import timeit

import numpy as np
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from kappa.database import (
    fetch_comics_by_ids,
    init_db,
    insert_ratings,
    list_comics,
    load_precomputed,
    upsert_comic_genres,
    upsert_comics,
)
from kappa.precompute import build_ratings_cluster, run_precompute
from kappa.predict import find_neighbor, predict

app = Flask(__name__)
CORS(app, allow_headers=["Content-Type", "X-API-Key"])  # allow frontend token header

API_TOKEN = os.environ.get("KAPPA_API_TOKEN")
KAPPA_USER_ID = "KAPPA_NEW_USER"

init_db()

_precomputed_cache = {}
_ready = threading.Event()


def _background_precompute():
    """Load or compute precomputed matrices for all methods at startup."""
    methods = ["kmeans", "dbscan"]
    for method in methods:
        try:
            loaded = load_precomputed(method)
            if loaded:
                _precomputed_cache[method] = {
                    "user_item_matrix": loaded["user_item_matrix"],
                    "cluster_labels": loaded["cluster_labels"],
                    "centroids": loaded["centroids"],
                    "computed_at": loaded["computed_at"],
                }
                print("Loaded existing precomputed data for {}".format(method))
            else:
                print("No precomputed data for {}, computing...".format(method))
                run_precompute(method)
                loaded = load_precomputed(method)
                if loaded:
                    _precomputed_cache[method] = {
                        "user_item_matrix": loaded["user_item_matrix"],
                        "cluster_labels": loaded["cluster_labels"],
                        "centroids": loaded["centroids"],
                        "computed_at": loaded["computed_at"],
                    }
                print("Precomputed data for {} ready".format(method))
        except Exception as exc:
            print("Error precomputing {}: {}".format(method, exc))
    _ready.set()
    print("Background precompute complete, service ready")


def start_precompute_thread():
    """Start the background precompute thread. Called from gunicorn post_fork hook."""
    t = threading.Thread(target=_background_precompute, daemon=True)
    t.start()
    return t


@app.before_request
def require_api_token():
    if request.method == "OPTIONS":
        return None
    if request.path in {"/", "/health", "/ready"}:
        return None
    if not API_TOKEN:
        return Response("Server token not configured", status=500)
    token = request.headers.get("X-API-Key")
    if token != API_TOKEN:
        return Response("Unauthorized", status=401)
    return None


def _normalize_comic_id(entry):
    if "comic_id" in entry:
        return int(entry["comic_id"])
    return int(entry["id"])


def _load_precomputed(method):
    cached = _precomputed_cache.get(method)
    if cached:
        return cached
    loaded = load_precomputed(method)
    if not loaded:
        return None
    cached = {
        "user_item_matrix": loaded["user_item_matrix"],
        "cluster_labels": loaded["cluster_labels"],
        "centroids": loaded["centroids"],
        "computed_at": loaded["computed_at"],
    }
    _precomputed_cache[method] = cached
    return cached


def _invalidate_precomputed_cache(method=None):
    if method:
        _precomputed_cache.pop(method, None)
        return
    _precomputed_cache.clear()


def _build_request_ratings_cluster(precomputed, user_input):
    user_item_matrix = precomputed["user_item_matrix"].copy()
    user_ratings = np.zeros(len(user_item_matrix.index))
    index_lookup = {
        comic_id: idx for idx, comic_id in enumerate(user_item_matrix.index)
    }
    rated_comics = []
    for entry in user_input:
        comic_id = _normalize_comic_id(entry)
        if comic_id in index_lookup:
            user_ratings[index_lookup[comic_id]] = float(entry["rating"])
            rated_comics.append(comic_id)
    user_item_matrix[KAPPA_USER_ID] = user_ratings
    ratings_cluster = build_ratings_cluster(
        user_item_matrix, precomputed["cluster_labels"]
    )
    return ratings_cluster, rated_comics


def _validate_user_input(user_input):
    if not isinstance(user_input, list):
        return "Expected JSON array"
    for entry in user_input:
        if not isinstance(entry, dict):
            return "Each entry must be an object"
        if "comic_id" not in entry and "id" not in entry:
            return "Each entry must include comic_id"
        if "rating" not in entry:
            return "Each entry must include rating"
    return None


def find_nearest_unrated(rated_comics, ratings_cluster):
    rated_comics = np.array(rated_comics)

    item_to_predict = []

    for item in rated_comics:
        if item not in ratings_cluster.index:
            continue
        which_cluster = ratings_cluster.loc[
            ratings_cluster.index == item, "cluster"
        ].iloc[0]
        clustered_ratings = ratings_cluster.loc[
            ratings_cluster["cluster"] == which_cluster
        ]

        item_to_predict.append(
            find_neighbor(
                item, clustered_ratings, usage="nearest_unrated", verbose=False
            )
        )

    item_to_predict = np.array(item_to_predict).flatten()  # convert the array into 1D
    item_to_predict = np.unique(item_to_predict)  # remove duplicate item
    item_to_predict = np.setdiff1d(item_to_predict, rated_comics)  # remove rated_comics

    return item_to_predict


@app.route("/", methods=["GET"])
def index():
    return "WELCOME TO KAPPA"


@app.route("/health")
def health():
    return Response("OK", status=200)


@app.route("/ready")
def ready():
    if _ready.is_set():
        return Response("OK", status=200)
    return Response("Precomputing", status=503)


@app.route("/api/kmeans", methods=["POST"])
def kmeans():
    # Receive the user input
    user_input = request.get_json()
    validation_error = _validate_user_input(user_input)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    print("User input received...")
    # Initialize an empty prediction list
    prediction_list = []

    start = timeit.default_timer()
    print("Processing Data...")
    precomputed = _load_precomputed("kmeans")
    if not precomputed:
        return jsonify({"error": "Precomputed data missing. Run /api/precompute."}), 503
    ratings_cluster, rated_comics = _build_request_ratings_cluster(
        precomputed, user_input
    )
    if not rated_comics:
        return jsonify({"error": "No rated comics matched the dataset"}), 400
    cluster_centroids = precomputed["centroids"]
    # Find nearest unrated item to predict
    item_to_predict = find_nearest_unrated(rated_comics, ratings_cluster)
    # Predict each item ratings
    for item in item_to_predict:
        print("Predicting {}".format(item))
        prediction = predict(
            KAPPA_USER_ID, item, ratings_cluster, cluster_centroids, verbose=False
        )
        if prediction["rating"] >= 3:
            prediction_list.append(prediction)
    if prediction_list:
        comic_map = fetch_comics_by_ids([item["id"] for item in prediction_list])
        for prediction in prediction_list:
            comic_info = comic_map.get(prediction["id"], {})
            prediction["title"] = comic_info.get("title")
            prediction["image_url"] = comic_info.get("image_url")
    # Sort the rating by descending order
    prediction_list = sorted(prediction_list, key=lambda i: i["rating"], reverse=True)
    end = timeit.default_timer()
    time = end - start
    print("\nPrediction Result:\n{}".format(prediction_list))
    print("Time Elapsed: {}".format(time))

    return jsonify(prediction_list)


@app.route("/api/dbscan", methods=["POST"])
def dbscan():
    # Receive the user input
    user_input = request.get_json()
    validation_error = _validate_user_input(user_input)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    print("User input received...")
    # Initialize an empty prediction list
    prediction_list = []

    start = timeit.default_timer()
    print("Processing Data...")
    precomputed = _load_precomputed("dbscan")
    if not precomputed:
        return jsonify({"error": "Precomputed data missing. Run /api/precompute."}), 503
    ratings_cluster, rated_comics = _build_request_ratings_cluster(
        precomputed, user_input
    )
    if not rated_comics:
        return jsonify({"error": "No rated comics matched the dataset"}), 400
    # Find nearest unrated item to predict
    item_to_predict = find_nearest_unrated(rated_comics, ratings_cluster)
    # Predict each item ratings
    for item in item_to_predict:
        print("Predicting {}".format(item))
        prediction = predict(
            KAPPA_USER_ID, item, ratings_cluster, centroids=None, verbose=False
        )
        if prediction["rating"] >= 3:
            prediction_list.append(prediction)
    if prediction_list:
        comic_map = fetch_comics_by_ids([item["id"] for item in prediction_list])
        for prediction in prediction_list:
            comic_info = comic_map.get(prediction["id"], {})
            prediction["title"] = comic_info.get("title")
            prediction["image_url"] = comic_info.get("image_url")
    # Sort the rating by descending order
    prediction_list = sorted(prediction_list, key=lambda i: i["rating"], reverse=True)
    end = timeit.default_timer()
    time = end - start
    print("\nPrediction Result:\n{}".format(prediction_list))
    print("Time Elapsed: {}".format(time))

    return jsonify(prediction_list)


@app.route("/api/comics", methods=["GET"])
def get_comics():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    return jsonify(list_comics(limit=limit, offset=offset))


@app.route("/api/comics/<int:comic_id>", methods=["GET"])
def get_comic(comic_id):
    result = fetch_comics_by_ids([comic_id])
    if comic_id not in result:
        return jsonify({"error": "Comic not found"}), 404
    return jsonify({"id": comic_id, **result[comic_id]})


@app.route("/api/comics", methods=["POST"])
def upsert_comics_handler():
    payload = request.get_json()
    if payload is None:
        return jsonify({"error": "Invalid JSON"}), 400
    entries = payload if isinstance(payload, list) else [payload]
    comics = []
    for entry in entries:
        if "comic_id" not in entry and "id" not in entry:
            return jsonify({"error": "comic_id is required"}), 400
        comics.append(
            {
                "comic_id": _normalize_comic_id(entry),
                "title": entry.get("title"),
                "image_url": entry.get("image_url"),
            }
        )
    count = upsert_comics(comics)
    return jsonify({"updated": count})


@app.route("/api/comics/genres", methods=["POST"])
def upsert_comic_genres_handler():
    payload = request.get_json()
    if payload is None:
        return jsonify({"error": "Invalid JSON"}), 400
    entries = payload if isinstance(payload, list) else [payload]
    genres = []
    for entry in entries:
        if "comic_id" not in entry and "id" not in entry:
            return jsonify({"error": "comic_id is required"}), 400
        genre_entry = {"comic_id": _normalize_comic_id(entry)}
        for key, value in entry.items():
            if key in {"comic_id", "id"}:
                continue
            genre_entry[key] = value
        genres.append(genre_entry)
    count = upsert_comic_genres(genres)
    return jsonify({"updated": count})


@app.route("/api/ratings", methods=["POST"])
def insert_ratings_handler():
    payload = request.get_json()
    if payload is None:
        return jsonify({"error": "Invalid JSON"}), 400
    entries = payload if isinstance(payload, list) else [payload]
    ratings = []
    for entry in entries:
        if "username" not in entry:
            return jsonify({"error": "username is required"}), 400
        if "comic_id" not in entry and "id" not in entry:
            return jsonify({"error": "comic_id is required"}), 400
        if "rating" not in entry:
            return jsonify({"error": "rating is required"}), 400
        ratings.append(
            {
                "username": entry["username"],
                "comic_id": _normalize_comic_id(entry),
                "rating": entry["rating"],
            }
        )
    count = insert_ratings(ratings)
    return jsonify({"inserted": count})


@app.route("/api/precompute", methods=["POST"])
def precompute_handler():
    payload = request.get_json(silent=True) or {}
    method = payload.get("method")
    results = []
    try:
        if method:
            results.append(run_precompute(method))
            _invalidate_precomputed_cache(method)
        else:
            results.append(run_precompute("kmeans"))
            results.append(run_precompute("dbscan"))
            _invalidate_precomputed_cache()
        return jsonify({"results": results})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/precompute/status", methods=["GET"])
def precompute_status_handler():
    response = {}
    for method in ["kmeans", "dbscan"]:
        loaded = load_precomputed(method)
        response[method] = loaded["computed_at"] if loaded else None
    return jsonify(response)
