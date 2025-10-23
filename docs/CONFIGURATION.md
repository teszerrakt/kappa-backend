# Configuration Reference

Complete reference for all configuration options in Kappa Backend.

## Table of Contents
- [Environment Variables](#environment-variables)
- [Flask Configuration](#flask-configuration)
- [Data Files](#data-files)
- [Algorithm Parameters](#algorithm-parameters)
- [Validation Settings](#validation-settings)
- [Logging](#logging)
- [CORS](#cors)
- [Rate Limiting](#rate-limiting)
- [Configuration Profiles](#configuration-profiles)

---

## Environment Variables

All configuration can be set via environment variables or `.env` file.

### Quick Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEBUG` | boolean | `False` | Enable debug mode |
| `HOST` | string | `0.0.0.0` | Server bind address |
| `PORT` | integer | `80` | Server port |
| `FLASK_ENV` | string | `production` | Flask environment |
| `DATA_DIR` | string | `/home/user/kappa-backend` | Data files directory |
| `RATING_FILE` | string | `rating_5_min_75.csv` | Rating data filename |
| `GENRE_FILE` | string | `comic_genre.csv` | Genre data filename |
| `COMIC_FILE` | string | `firestore_comics.csv` | Comic metadata filename |
| `KMEANS_CLUSTERS` | integer | `2` | Number of K-Means clusters |
| `DBSCAN_EPSILON` | float | `7.8` | DBSCAN epsilon parameter |
| `KNN_K` | integer | `10` | Number of nearest neighbors |
| `MIN_RATING_THRESHOLD` | float | `3.0` | Minimum rating to recommend |
| `MIN_USER_RATINGS` | integer | `5` | Minimum input ratings required |
| `MAX_USER_RATINGS` | integer | `1000` | Maximum input ratings allowed |
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `CORS_ORIGINS` | string | `*` | Allowed CORS origins |
| `RATE_LIMIT_ENABLED` | boolean | `True` | Enable rate limiting |
| `RATE_LIMIT_DEFAULT` | string | `100 per hour` | Default rate limit |

---

## Flask Configuration

### DEBUG

```bash
DEBUG=False  # Production
DEBUG=True   # Development
```

**Description:** Enables Flask debug mode with auto-reload and detailed error pages.

**⚠️ Warning:** Never enable debug mode in production! It exposes sensitive information and poses security risks.

**When to use:**
- `False` - Production deployments
- `True` - Local development only

---

### HOST

```bash
HOST=0.0.0.0    # Listen on all interfaces
HOST=127.0.0.1  # Listen on localhost only
```

**Description:** Server bind address.

**Common values:**
- `0.0.0.0` - Accept connections from any IP (Docker, production)
- `127.0.0.1` - Accept local connections only (development)

---

### PORT

```bash
PORT=80     # Standard HTTP
PORT=8000   # Alternative port
PORT=443    # HTTPS (requires SSL config)
```

**Description:** Server port number.

**Note:** Ports < 1024 require root/admin privileges on most systems.

---

### FLASK_ENV

```bash
FLASK_ENV=production   # Production
FLASK_ENV=development  # Development
FLASK_ENV=test         # Testing
```

**Description:** Flask environment mode.

**Effects:**
- `production` - Optimized for performance, minimal logging
- `development` - Debug mode, auto-reload, verbose logging
- `test` - Optimized for testing

---

## Data Files

### DATA_DIR

```bash
DATA_DIR=/home/user/kappa-backend
DATA_DIR=/app  # Docker
DATA_DIR=/data  # Custom location
```

**Description:** Base directory for data files.

**Requirements:**
- Must be readable by application
- Must contain all three CSV files
- Recommended: Absolute path

---

### RATING_FILE

```bash
RATING_FILE=rating_5_min_75.csv
```

**Description:** User ratings data file.

**Format:**
```csv
username,comicID,rating
user1,44489,5.0
user2,72025,4.5
...
```

**Columns:**
- `username` (string): User identifier
- `comicID` (integer): Comic identifier
- `rating` (float): Rating value (1.0-5.0)

**Size:** ~150K records (15MB+)

---

### GENRE_FILE

```bash
GENRE_FILE=comic_genre.csv
```

**Description:** Comic genre features for clustering.

**Format:**
```csv
comicID,action,adventure,comedy,drama,fantasy,horror,romance,sci-fi,...
44489,1,0,1,0,1,0,0,0
72025,1,1,0,0,1,0,0,0
...
```

**Columns:**
- `comicID` (integer): Comic identifier
- Genre columns (0/1): Binary genre indicators

**Size:** ~13K records

---

### COMIC_FILE

```bash
COMIC_FILE=firestore_comics.csv
```

**Description:** Comic metadata (titles and images).

**Format:**
```csv
comic_id,title,image_url
44489,Naruto,https://example.com/naruto.jpg
72025,One Piece,https://example.com/onepiece.jpg
...
```

**Columns:**
- `comic_id` (integer): Comic identifier
- `title` (string): Comic title
- `image_url` (string): Cover image URL

**Size:** ~900 records

---

## Algorithm Parameters

### KMEANS_CLUSTERS

```bash
KMEANS_CLUSTERS=2   # Default
KMEANS_CLUSTERS=3   # More granular
KMEANS_CLUSTERS=5   # Fine-grained
```

**Description:** Number of clusters for K-Means algorithm.

**Range:** 1 to N (where N < number of comics)

**Effects:**
- **Lower values (2-3):** Broader recommendations, faster computation
- **Higher values (5-10):** More specific recommendations, slower computation

**Recommendations:**
- Small datasets: 2-3 clusters
- Large datasets: 3-5 clusters
- Experiment to find optimal value

**Trade-offs:**
| Clusters | Speed | Accuracy | Recommendation Diversity |
|----------|-------|----------|--------------------------|
| 2 | Fast | Moderate | High |
| 3-5 | Moderate | Good | Moderate |
| 5+ | Slow | High | Low |

---

### DBSCAN_EPSILON

```bash
DBSCAN_EPSILON=7.8   # Default
DBSCAN_EPSILON=5.0   # Tighter clusters
DBSCAN_EPSILON=10.0  # Looser clusters
```

**Description:** Maximum distance between two samples to be considered neighbors in DBSCAN.

**Range:** 0.1 to 20.0 (typical)

**Effects:**
- **Lower values:** Tighter, more numerous clusters
- **Higher values:** Looser, fewer clusters

**Tuning guide:**
- Start with default (7.8)
- If too many noise points: Increase epsilon
- If clusters too large: Decrease epsilon

---

### KNN_K

```bash
KNN_K=10   # Default
KNN_K=5    # Fewer neighbors
KNN_K=20   # More neighbors
```

**Description:** Number of nearest neighbors for collaborative filtering.

**Range:** 1 to 100

**Effects:**
- **Lower K (5-10):**
  - More personalized recommendations
  - Sensitive to outliers
  - Faster computation
- **Higher K (20-50):**
  - More stable predictions
  - Less personalized
  - Slower computation

**Recommendations:**
- Small datasets: K = 5-10
- Large datasets: K = 10-20
- Sparse data: Increase K
- Dense data: Decrease K

---

### MIN_RATING_THRESHOLD

```bash
MIN_RATING_THRESHOLD=3.0   # Default (recommend if rating ≥ 3)
MIN_RATING_THRESHOLD=3.5   # Higher quality recommendations
MIN_RATING_THRESHOLD=2.5   # More recommendations
```

**Description:** Minimum predicted rating to include in recommendations.

**Range:** 0.0 to 5.0

**Effects:**
- **Lower threshold (2.0-2.5):**
  - More recommendations
  - Lower average quality
- **Higher threshold (3.5-4.0):**
  - Fewer recommendations
  - Higher average quality

**Recommendation:** Keep at 3.0 for balanced results

---

## Validation Settings

### MIN_USER_RATINGS

```bash
MIN_USER_RATINGS=5    # Default
MIN_USER_RATINGS=3    # More permissive
MIN_USER_RATINGS=10   # More strict
```

**Description:** Minimum number of ratings required from user.

**Range:** 1 to MAX_USER_RATINGS

**Effects:**
- **Too low (<3):** Unreliable recommendations
- **Too high (>10):** Reduces user adoption

**Recommendation:** 5 ratings provides good balance

---

### MAX_USER_RATINGS

```bash
MAX_USER_RATINGS=1000   # Default
MAX_USER_RATINGS=100    # Stricter limit
MAX_USER_RATINGS=5000   # More permissive
```

**Description:** Maximum number of ratings accepted from user.

**Range:** MIN_USER_RATINGS to unlimited

**Purpose:**
- Prevent denial-of-service attacks
- Limit computation time
- Control memory usage

---

## Logging

### LOG_LEVEL

```bash
LOG_LEVEL=DEBUG    # All messages
LOG_LEVEL=INFO     # Informational messages
LOG_LEVEL=WARNING  # Warnings and errors
LOG_LEVEL=ERROR    # Errors only
LOG_LEVEL=CRITICAL # Critical errors only
```

**Description:** Minimum logging level.

**Levels (most to least verbose):**

| Level | When to Use | Output |
|-------|-------------|--------|
| `DEBUG` | Development, troubleshooting | All debug + info + warning + error messages |
| `INFO` | Production (default) | Info + warning + error messages |
| `WARNING` | Production (quiet) | Warning + error messages only |
| `ERROR` | Production (minimal) | Error messages only |
| `CRITICAL` | Production (silent) | Critical errors only |

**Example log output:**

```
DEBUG level:
2024-01-20 10:30:15 - main - DEBUG - [process_recommendations:115] - Processing recommendations using KMEANS algorithm
2024-01-20 10:30:15 - utils - DEBUG - [find_nearest_unrated:25] - Finding nearest unrated items
2024-01-20 10:30:16 - predict - DEBUG - [predict:150] - Predicting rating for item 598

INFO level:
2024-01-20 10:30:15 - main - INFO - [process_recommendations:113] - Processing recommendations using KMEANS algorithm
2024-01-20 10:30:16 - cluster - INFO - [kmeans_clustering:65] - K-Means clustering completed: 2 clusters created
2024-01-20 10:30:17 - main - INFO - [process_recommendations:180] - Generated 15 recommendations
```

---

## CORS

### CORS_ORIGINS

```bash
CORS_ORIGINS=*                                     # Allow all origins (development)
CORS_ORIGINS=https://example.com                   # Single origin
CORS_ORIGINS=https://example.com,https://app.com   # Multiple origins
```

**Description:** Allowed Cross-Origin Resource Sharing origins.

**⚠️ Security Warning:**
- **Never use `*` in production!**
- Specify exact domains that should access your API

**Examples:**

Development:
```bash
CORS_ORIGINS=http://localhost:3000
```

Production:
```bash
CORS_ORIGINS=https://kappa.zsyihab.tech
```

Multiple domains:
```bash
CORS_ORIGINS=https://kappa.zsyihab.tech,https://app.kappa.com
```

---

## Rate Limiting

### RATE_LIMIT_ENABLED

```bash
RATE_LIMIT_ENABLED=True   # Enable rate limiting
RATE_LIMIT_ENABLED=False  # Disable (development only)
```

**Description:** Enable/disable request rate limiting.

**Recommendation:** Always enabled in production

---

### RATE_LIMIT_DEFAULT

```bash
RATE_LIMIT_DEFAULT=100 per hour    # Default
RATE_LIMIT_DEFAULT=50 per hour     # More strict
RATE_LIMIT_DEFAULT=200 per hour    # More permissive
RATE_LIMIT_DEFAULT=10 per minute   # Fine-grained control
```

**Description:** Default rate limit for API endpoints.

**Format:** `<count> per <period>`

**Periods:** `second`, `minute`, `hour`, `day`

**Examples:**
```bash
RATE_LIMIT_DEFAULT=5 per second
RATE_LIMIT_DEFAULT=100 per hour
RATE_LIMIT_DEFAULT=1000 per day
```

---

## Configuration Profiles

### Development Profile

```bash
# .env.development
DEBUG=True
HOST=127.0.0.1
PORT=80
FLASK_ENV=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_ENABLED=False
MIN_USER_RATINGS=3
KMEANS_CLUSTERS=2
```

**Use case:** Local development and testing

---

### Production Profile

```bash
# .env.production
DEBUG=False
HOST=0.0.0.0
PORT=80
FLASK_ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://kappa.zsyihab.tech
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=50 per hour
MIN_USER_RATINGS=5
KMEANS_CLUSTERS=2
DBSCAN_EPSILON=7.8
KNN_K=10
MIN_RATING_THRESHOLD=3.0
```

**Use case:** Production deployment

---

### Testing Profile

```bash
# .env.test
DEBUG=True
FLASK_ENV=test
LOG_LEVEL=DEBUG
DATA_DIR=./test_data
RATE_LIMIT_ENABLED=False
MIN_USER_RATINGS=1
```

**Use case:** Automated testing

---

## Configuration Validation

The application validates configuration on startup:

```python
# Automatic validation
Config.validate()
```

**Checks:**
1. Required data files exist
2. Hyperparameters are valid ranges
3. Paths are accessible

**Failure behavior:**
- Application will not start if validation fails
- Error message indicates which configuration is invalid

---

## Docker Configuration

### Environment Variables in Docker

```bash
docker run -d \
  -e DEBUG=False \
  -e LOG_LEVEL=info \
  -e KMEANS_CLUSTERS=2 \
  -e CORS_ORIGINS=https://example.com \
  kappa-backend:latest
```

### Docker Compose

```yaml
services:
  kappa-backend:
    image: kappa-backend:latest
    environment:
      DEBUG: "False"
      LOG_LEVEL: "info"
      KMEANS_CLUSTERS: "2"
      DBSCAN_EPSILON: "7.8"
      KNN_K: "10"
```

### Environment File

```yaml
services:
  kappa-backend:
    env_file:
      - .env.production
```

---

## Best Practices

### Security

✅ **Do:**
- Set `DEBUG=False` in production
- Specify exact `CORS_ORIGINS` (not `*`)
- Enable `RATE_LIMIT_ENABLED=True`
- Use `INFO` or `WARNING` log level in production
- Secure `.env` file (never commit to git)

❌ **Don't:**
- Never set `DEBUG=True` in production
- Never use `CORS_ORIGINS=*` in production
- Never disable rate limiting in production
- Never expose sensitive config in logs

---

### Performance

**For optimal performance:**

```bash
# Moderate cluster count
KMEANS_CLUSTERS=2-3

# Balanced KNN
KNN_K=10

# Reasonable threshold
MIN_RATING_THRESHOLD=3.0

# Appropriate log level
LOG_LEVEL=INFO
```

**For faster responses (sacrifice some accuracy):**

```bash
KMEANS_CLUSTERS=2
KNN_K=5
MIN_RATING_THRESHOLD=2.5
```

**For better accuracy (slower responses):**

```bash
KMEANS_CLUSTERS=5
KNN_K=20
MIN_RATING_THRESHOLD=3.5
```

---

## Troubleshooting

### Configuration not loading

**Check:**
1. `.env` file in correct directory
2. Environment variables properly exported
3. No syntax errors in `.env` file
4. File permissions allow reading

### Invalid configuration errors

**Common issues:**
```bash
# Wrong: String instead of number
KMEANS_CLUSTERS="two"  # ❌

# Correct: Numeric value
KMEANS_CLUSTERS=2      # ✅

# Wrong: Boolean as string without quotes
DEBUG=False            # ✅ (works but inconsistent)

# Better: Lowercase string
DEBUG=false            # ✅ (recommended)
```

### Data files not found

**Check:**
1. `DATA_DIR` points to correct directory
2. File names match exactly (case-sensitive)
3. Files have read permissions
4. Full paths are correct

---

## Environment Variable Precedence

Configuration is loaded in this order (later overrides earlier):

1. Default values in `config.py`
2. `.env` file
3. Environment variables
4. Command-line arguments (if implemented)

Example:
```bash
# config.py default
KMEANS_CLUSTERS = 2

# .env file
KMEANS_CLUSTERS=3

# Environment variable
export KMEANS_CLUSTERS=4

# Final value: 4 (environment variable wins)
```

---

## References

- [Flask Configuration](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Environment Variables Best Practices](https://12factor.net/config)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
