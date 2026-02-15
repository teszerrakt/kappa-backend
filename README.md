# Kappa Backend

REST API for Kappa, a cluster-based comic recommender using K-Means/DBSCAN + KNN.

## Project Structure
```
kappa-backend/
  src/
    kappa/        # App code (Flask routes + ML pipeline)
    scripts/      # Maintenance scripts (migration)
  tests/          # Pytest suite
  wsgi.py         # Gunicorn entrypoint
  run.sh          # Prod runner
  *.csv           # Seed data files
```

## Quick Start

### Local (uv)
```bash
uv venv
uv pip install -r requirements.txt
uv pip sync uv.lock
export PYTHONPATH=./src
python src/scripts/migrate.py
python wsgi.py
```

### Makefile shortcuts
```bash
make venv
make sync
make migrate
make run
```

### Tests
```bash
uv venv
uv pip install -r requirements.txt
uv pip sync uv.lock
pytest
```

### Production (Gunicorn)
```bash
bash run.sh
```

### Docker
```bash
docker build -t kappa-api .
docker run -p 80:80 kappa-api
```

## API Endpoints

### Core
- `GET /` -> `WELCOME TO KAPPA`
- `GET /health` -> `OK`
- `POST /api/kmeans` -> recommendations via K-Means
- `POST /api/dbscan` -> recommendations via DBSCAN

### Data management
- `GET /api/comics` -> list comics
- `GET /api/comics/<id>` -> comic details
- `POST /api/comics` -> insert/update comics
- `POST /api/comics/genres` -> insert/update genre flags
- `POST /api/ratings` -> insert ratings

### Precompute
- `POST /api/precompute` -> compute clustering caches
- `GET /api/precompute/status` -> last compute timestamps

## Request Input
Recommendation requests expect a JSON array with `comic_id` (or `id`) and `rating`:
```json
[
  {"comic_id": 44489, "rating": 5},
  {"comic_id": 72025, "rating": 4}
]
```

## Notes
- Recommendations require precomputed data. Call `POST /api/precompute` after seeding or data changes.
- The SQLite database path is controlled via `KAPPA_DB_PATH` (default: `kappa.db`).
