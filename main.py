"""
Kappa Backend API - Comic Recommendation System

This Flask application provides endpoints for comic recommendations using
collaborative filtering with K-Means and DBSCAN clustering algorithms.
"""
from typing import Dict, Any, List, Optional, Tuple
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd

from config import Config
from logger import setup_logger, get_logger
from validation import validate_user_input, ValidationError
from utils import (
    find_nearest_unrated,
    enrich_prediction_with_metadata,
    filter_and_sort_predictions,
    load_csv_data,
    Timer
)
from load_data import merge_user_rating, load_rating_data
from cluster import kmeans_clustering, dbscan_clustering
from predict import find_neighbor, predict

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# Setup logging
logger = setup_logger(__name__, Config.LOG_LEVEL)

# Global data storage
_data_cache = {}


def initialize_data() -> None:
    """
    Initialize and load all required data files.

    Raises:
        FileNotFoundError: If required data files are not found
        pd.errors.ParserError: If CSV parsing fails
    """
    global _data_cache

    try:
        # Validate configuration
        Config.validate()

        # Load data files
        rating_file = Config.get_file_path(Config.RATING_FILE)
        genre_file = Config.get_file_path(Config.GENRE_FILE)
        comic_file = Config.get_file_path(Config.COMIC_FILE)

        all_data, comic_genre, comic_data = load_csv_data(
            rating_file, genre_file, comic_file
        )

        _data_cache = {
            'all_data': all_data,
            'comic_genre': comic_genre,
            'comic_data': comic_data
        }

        logger.info("Data initialization completed successfully")

    except Exception as e:
        logger.error(f"Failed to initialize data: {e}")
        raise


def get_data(key: str) -> pd.DataFrame:
    """
    Get cached data by key.

    Args:
        key: Data key ('all_data', 'comic_genre', 'comic_data')

    Returns:
        Requested DataFrame

    Raises:
        RuntimeError: If data not initialized
    """
    if not _data_cache:
        raise RuntimeError("Data not initialized. Call initialize_data() first.")

    return _data_cache.get(key)


def process_recommendations(
    user_input: List[Dict[str, Any]],
    algorithm: str,
    centroids: Optional[pd.DataFrame] = None
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Process recommendations using specified clustering algorithm.

    This is the core DRY function that handles both KMeans and DBSCAN algorithms.

    Args:
        user_input: List of user rating dictionaries
        algorithm: Clustering algorithm ('kmeans' or 'dbscan')
        centroids: Cluster centroids (required for KMeans, None for DBSCAN)

    Returns:
        Tuple of (predictions list, elapsed time in seconds)

    Raises:
        ValueError: If invalid algorithm specified
    """
    logger.info(f"Processing recommendations using {algorithm.upper()} algorithm")

    with Timer(f"{algorithm.upper()} recommendation") as timer:
        # Merge user input with historical data
        logger.debug("Merging user ratings with historical data")
        rating_data = merge_user_rating(user_input, get_data('all_data'))

        # Load and prepare data for clustering
        logger.debug("Loading rating data for clustering")
        rating_data, cluster_data = load_rating_data(
            get_data('comic_genre'), rating_data
        )

        # Perform clustering based on algorithm
        if algorithm == 'kmeans':
            logger.debug(f"Performing K-Means clustering with {Config.KMEANS_CLUSTERS} clusters")
            ratings_cluster, cluster_centroids = kmeans_clustering(
                Config.KMEANS_CLUSTERS, cluster_data, rating_data
            )
        elif algorithm == 'dbscan':
            logger.debug(f"Performing DBSCAN clustering with epsilon={Config.DBSCAN_EPSILON}")
            ratings_cluster = dbscan_clustering(
                Config.DBSCAN_EPSILON, cluster_data, rating_data
            )
            cluster_centroids = None
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Find items to predict
        logger.debug("Finding nearest unrated items")
        items_to_predict = find_nearest_unrated(
            user_input, ratings_cluster, find_neighbor
        )

        logger.info(f"Found {len(items_to_predict)} items to predict")

        # Generate predictions
        prediction_list = []
        for item in items_to_predict:
            try:
                logger.debug(f"Predicting rating for item {item}")
                prediction = predict(
                    "KAPPA_NEW_USER",
                    item,
                    ratings_cluster,
                    centroids=cluster_centroids,
                    k=Config.KNN_K,
                    verbose=False
                )

                # Enrich with metadata
                enriched = enrich_prediction_with_metadata(
                    prediction, get_data('comic_data')
                )

                if enriched:
                    prediction_list.append(enriched)

            except Exception as e:
                logger.warning(f"Failed to predict rating for item {item}: {e}")
                continue

        # Filter and sort predictions
        final_predictions = filter_and_sort_predictions(
            prediction_list, Config.MIN_RATING_THRESHOLD
        )

        logger.info(f"Generated {len(final_predictions)} recommendations")

    return final_predictions, timer.elapsed


@app.route('/', methods=['GET'])
def index() -> str:
    """Root endpoint returning welcome message."""
    return "WELCOME TO KAPPA"


@app.route('/health', methods=['GET'])
def health() -> Response:
    """
    Health check endpoint with detailed status.

    Returns:
        JSON response with health status and data information
    """
    try:
        status = {
            'status': 'healthy',
            'service': 'kappa-backend',
            'data_loaded': bool(_data_cache),
        }

        if _data_cache:
            status['data_stats'] = {
                'ratings': len(get_data('all_data')),
                'genres': len(get_data('comic_genre')),
                'comics': len(get_data('comic_data'))
            }

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/api/kmeans', methods=['POST'])
def kmeans() -> Tuple[Response, int]:
    """
    Generate comic recommendations using K-Means clustering.

    Request Body:
        List of rating dictionaries with 'id', 'rating', and 'title' keys

    Returns:
        JSON response with recommended comics sorted by predicted rating

    Example:
        POST /api/kmeans
        [
            {"id": 1, "rating": 5.0, "title": "Comic Title"},
            {"id": 2, "rating": 4.0, "title": "Another Comic"}
        ]
    """
    try:
        # Get and validate user input
        user_input = request.get_json()
        logger.info(f"K-Means recommendation request received with {len(user_input) if user_input else 0} ratings")

        validated_input = validate_user_input(user_input)

        # Process recommendations
        predictions, elapsed_time = process_recommendations(
            validated_input, algorithm='kmeans'
        )

        # Log results
        logger.info(
            f"K-Means request completed: {len(predictions)} recommendations "
            f"in {elapsed_time:.2f}s"
        )

        return jsonify(predictions), 200

    except ValidationError as e:
        logger.warning(f"Validation error in K-Means endpoint: {e}")
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        logger.error(f"Error in K-Means endpoint: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/dbscan', methods=['POST'])
def dbscan() -> Tuple[Response, int]:
    """
    Generate comic recommendations using DBSCAN clustering.

    Request Body:
        List of rating dictionaries with 'id', 'rating', and 'title' keys

    Returns:
        JSON response with recommended comics sorted by predicted rating

    Example:
        POST /api/dbscan
        [
            {"id": 1, "rating": 5.0, "title": "Comic Title"},
            {"id": 2, "rating": 4.0, "title": "Another Comic"}
        ]
    """
    try:
        # Get and validate user input
        user_input = request.get_json()
        logger.info(f"DBSCAN recommendation request received with {len(user_input) if user_input else 0} ratings")

        validated_input = validate_user_input(user_input)

        # Process recommendations
        predictions, elapsed_time = process_recommendations(
            validated_input, algorithm='dbscan'
        )

        # Log results
        logger.info(
            f"DBSCAN request completed: {len(predictions)} recommendations "
            f"in {elapsed_time:.2f}s"
        )

        return jsonify(predictions), 200

    except ValidationError as e:
        logger.warning(f"Validation error in DBSCAN endpoint: {e}")
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        logger.error(f"Error in DBSCAN endpoint: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# Initialize data on module load
try:
    initialize_data()
except Exception as e:
    logger.critical(f"Failed to start application: {e}")
    raise


if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
