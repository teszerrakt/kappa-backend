# AGENTS.md - Kappa Backend

## Project Overview

Kappa is a **cluster-based comic recommender system** backend built with **Python/Flask**.
It exposes a REST API that accepts user comic ratings and returns recommendations
using K-Means or DBSCAN clustering combined with KNN-based collaborative filtering.

**Python version:** 3.11+ (uv/venv supported)
**Framework:** Flask with Gunicorn (WSGI)

## Project Structure

```
kappa-backend/
  src/
    kappa/         # Flask app + ML pipeline
    scripts/       # Migration and maintenance scripts
  tests/           # Pytest suite
  wsgi.py          # Gunicorn WSGI entry point
  run.sh           # Shell script to start gunicorn
  requirements.txt # Python dependencies (flask, pandas, numpy, scikit-learn, etc.)
  Dockerfile       # Container build definition
  *.csv            # Data files (ratings, comic genres, comic metadata)
```

## Build & Run Commands

### Install dependencies
```bash
uv venv
uv pip install -r requirements.txt
uv pip sync uv.lock
```

### Run development server
```bash
export PYTHONPATH=./src
python wsgi.py
```

### Run production server (Gunicorn)
```bash
bash run.sh
# equivalent to: gunicorn wsgi:app --bind 0.0.0.0:80 --log-level=debug --workers=2
```

### Docker
```bash
docker build -t kappa-api .
docker run -p 80:80 kappa-api
```

## Testing

Tests use `pytest` and live under `tests/`.
```bash
pytest
pytest tests/test_cluster.py
pytest tests/test_cluster.py::test_kmeans_clustering
pytest -v
```

## Linting & Formatting

**No linter or formatter is configured.** There is no flake8, pylint, black,
isort, or pyproject.toml in the project.

### If adding linting/formatting
- Use `black` for formatting and `flake8` for linting
- Run: `black .` and `flake8 .`

## API Endpoints

| Method | Path           | Description                                  |
|--------|----------------|----------------------------------------------|
| GET    | `/`            | Returns `"WELCOME TO KAPPA"`                 |
| GET    | `/health`      | Health check, returns `"OK"` with status 200 |
| POST   | `/api/kmeans`  | Recommendations via K-Means clustering       |
| POST   | `/api/dbscan`  | Recommendations via DBSCAN clustering        |

### Request format (POST endpoints)
```json
[
  {"id": 44489, "rating": 5, "title": "Some Comic"},
  {"id": 72025, "rating": 4, "title": "Another Comic"}
]
```

### Response format
```json
[
  {"id": 12345, "rating": 4.2, "title": "Comic Title", "image_url": "https://..."}
]
```

## Code Style Guidelines

### Imports
- Standard library imports first (`timeit`)
- Third-party imports next (`flask`, `pandas`, `numpy`, `sklearn`)
- Local imports last (`from kappa.load_data import ...`, `from kappa.cluster import ...`)
- Use specific imports: `from flask import Flask, request, jsonify, Response`
- Alias conventions: `pandas as pd`, `numpy as np`

### Naming Conventions
- **Functions:** `snake_case` (e.g., `find_nearest_unrated`, `merge_user_rating`)
- **Variables:** `snake_case` (e.g., `rating_data`, `cluster_data`)
- **Constants / global data:** `snake_case` at module level (e.g., `all_data`, `comic_genre`)
- **Route functions:** short `snake_case` names matching the endpoint (e.g., `def kmeans():`)
- **Parameters:** `snake_case`, use descriptive names (e.g., `item_id`, `user_id`, `ratings_cluster`)

### Formatting
- 4-space indentation (standard Python)
- No trailing whitespace enforcement configured
- Comments use `#` with a space, placed above or inline with code
- Docstrings are not used in the current codebase; prefer adding them for new functions
- Line length is not enforced but generally stays under 120 characters

### Types
- No type annotations are used in the existing codebase
- When adding new code, type hints are encouraged but not required
- Key data types used throughout:
  - `pd.DataFrame` for tabular data (ratings, clusters, genres)
  - `np.ndarray` for numeric arrays
  - `list[dict]` for API request/response payloads
  - `dict` with `"id"` (int) and `"rating"` (float) for prediction results

### Error Handling
- Minimal error handling in the current codebase
- Flask's default error handling is relied upon
- No try/except blocks are used in existing code
- When adding new code, handle at minimum:
  - Invalid JSON input (400 errors)
  - Missing required fields in request data
  - Items not found in dataset (KeyError from pandas)
- Return errors as JSON: `jsonify({"error": "message"}), 400`

### Function Design
- Functions accept DataFrames and return DataFrames or tuples
- Use `verbose=False` parameter pattern for optional debug printing
- Use `print()` for logging (no logging framework configured)
- Return dictionaries for API-facing data (e.g., `{"id": int, "rating": float}`)

### Data Flow Pattern
The recommendation pipeline follows this sequence:
1. `merge_user_rating()` - merge user input with existing ratings
2. `load_rating_data()` - create user-item matrix and cluster dataset
3. `kmeans_clustering()` / `dbscan_clustering()` - cluster the items
4. `find_nearest_unrated()` - find candidate items to predict
5. `predict()` - predict ratings using KNN collaborative filtering
6. Filter predictions >= 3.0, sort descending, return as JSON

### CSV Data Files
- `rating_5_min_75.csv` - User ratings (columns: username, comicID, rating)
- `comic_genre.csv` - Comic genre features for clustering
- `firestore_comics.csv` - Comic metadata (comic_id, title, image_url)
- CSVs are used for migration/seed only. Runtime data is stored in SQLite.
- Do NOT commit large data file changes without discussion

### Git & Version Control
- `.gitignore` excludes: `__pycache__/`, `test_main.ipynb`, `.venv`
- Do not commit `.env` files, virtual environments, or IDE configs
- Do not commit changes to CSV data files unless intentional
