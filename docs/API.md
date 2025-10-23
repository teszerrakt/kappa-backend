# API Documentation

Kappa Backend provides RESTful endpoints for comic recommendations using collaborative filtering with clustering algorithms.

## Base URL

```
http://localhost:80
```

---

## Endpoints

### 1. Welcome Message

```http
GET /
```

Returns a welcome message.

**Response:**
```
WELCOME TO KAPPA
```

**Status Codes:**
- `200 OK` - Success

---

### 2. Health Check

```http
GET /health
```

Returns the health status of the service and data statistics.

**Response:**
```json
{
  "status": "healthy",
  "service": "kappa-backend",
  "data_loaded": true,
  "data_stats": {
    "ratings": 151774,
    "genres": 13278,
    "comics": 913
  }
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is unhealthy

---

### 3. K-Means Recommendations

```http
POST /api/kmeans
```

Generate comic recommendations using K-Means clustering algorithm.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
[
  {
    "id": 44489,
    "rating": 5.0,
    "title": "Naruto"
  },
  {
    "id": 72025,
    "rating": 4.5,
    "title": "One Piece"
  },
  {
    "id": 13,
    "rating": 5.0,
    "title": "Attack on Titan"
  },
  {
    "id": 21,
    "rating": 4.0,
    "title": "Death Note"
  },
  {
    "id": 1706,
    "rating": 4.5,
    "title": "Fullmetal Alchemist"
  }
]
```

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | Comic ID |
| rating | float | Yes | User rating (1.0 - 5.0) |
| title | string | No | Comic title (optional, for reference) |

**Constraints:**
- Minimum 5 ratings required (configurable via `MIN_USER_RATINGS`)
- Maximum 1000 ratings allowed (configurable via `MAX_USER_RATINGS`)
- Rating values must be between 1.0 and 5.0

**Response:**
```json
[
  {
    "id": 598,
    "rating": 4.8234,
    "title": "Hunter x Hunter",
    "image_url": "https://example.com/image1.jpg"
  },
  {
    "id": 1535,
    "rating": 4.6521,
    "title": "My Hero Academia",
    "image_url": "https://example.com/image2.jpg"
  },
  {
    "id": 2904,
    "rating": 4.5123,
    "title": "Demon Slayer",
    "image_url": "https://example.com/image3.jpg"
  }
]
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Comic ID |
| rating | float | Predicted rating |
| title | string | Comic title |
| image_url | string | Comic cover image URL |

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input (see error response)
- `500 Internal Server Error` - Server error

**Error Response:**
```json
{
  "error": "At least 5 ratings are required, got 3"
}
```

---

### 4. DBSCAN Recommendations

```http
POST /api/dbscan
```

Generate comic recommendations using DBSCAN (Density-Based Spatial Clustering) algorithm.

**Request/Response Format:** Identical to K-Means endpoint (see above)

**Algorithm Differences:**
- DBSCAN uses density-based clustering instead of centroid-based
- Can identify noise points (outliers)
- Automatically determines number of clusters
- May produce different recommendations compared to K-Means

---

## Error Handling

All endpoints return proper HTTP status codes and error messages.

### Validation Errors (400 Bad Request)

```json
{
  "error": "Validation error message"
}
```

**Common Validation Errors:**
- `Request body is required`
- `Input must be a list of ratings`
- `At least N ratings are required, got M`
- `Rating at index X missing required field: Y`
- `Rating at index X: 'rating' must be between 1.0 and 5.0, got Z`

### Server Errors (500 Internal Server Error)

```json
{
  "error": "Internal server error"
}
```

Server errors are logged with full stack traces for debugging.

---

## Examples

### cURL Examples

**K-Means Recommendation:**
```bash
curl -X POST http://localhost:80/api/kmeans \
  -H "Content-Type: application/json" \
  -d '[
    {"id": 44489, "rating": 5.0, "title": "Naruto"},
    {"id": 72025, "rating": 4.5, "title": "One Piece"},
    {"id": 13, "rating": 5.0, "title": "Attack on Titan"},
    {"id": 21, "rating": 4.0, "title": "Death Note"},
    {"id": 1706, "rating": 4.5, "title": "Fullmetal Alchemist"}
  ]'
```

**DBSCAN Recommendation:**
```bash
curl -X POST http://localhost:80/api/dbscan \
  -H "Content-Type: application/json" \
  -d '[
    {"id": 44489, "rating": 5.0},
    {"id": 72025, "rating": 4.5},
    {"id": 13, "rating": 5.0},
    {"id": 21, "rating": 4.0},
    {"id": 1706, "rating": 4.5}
  ]'
```

**Health Check:**
```bash
curl http://localhost:80/health
```

### Python Example

```python
import requests

# Prepare user ratings
ratings = [
    {"id": 44489, "rating": 5.0, "title": "Naruto"},
    {"id": 72025, "rating": 4.5, "title": "One Piece"},
    {"id": 13, "rating": 5.0, "title": "Attack on Titan"},
    {"id": 21, "rating": 4.0, "title": "Death Note"},
    {"id": 1706, "rating": 4.5, "title": "Fullmetal Alchemist"}
]

# Get recommendations
response = requests.post(
    'http://localhost:80/api/kmeans',
    json=ratings
)

if response.status_code == 200:
    recommendations = response.json()
    for comic in recommendations:
        print(f"{comic['title']}: {comic['rating']:.2f}")
else:
    print(f"Error: {response.json()['error']}")
```

### JavaScript Example

```javascript
const ratings = [
  { id: 44489, rating: 5.0, title: "Naruto" },
  { id: 72025, rating: 4.5, title: "One Piece" },
  { id: 13, rating: 5.0, title: "Attack on Titan" },
  { id: 21, rating: 4.0, title: "Death Note" },
  { id: 1706, rating: 4.5, title: "Fullmetal Alchemist" }
];

fetch('http://localhost:80/api/kmeans', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(ratings)
})
  .then(response => response.json())
  .then(recommendations => {
    recommendations.forEach(comic => {
      console.log(`${comic.title}: ${comic.rating.toFixed(2)}`);
    });
  })
  .catch(error => console.error('Error:', error));
```

---

## Rate Limiting

Rate limiting can be enabled via configuration (see Configuration Reference).

Default: 100 requests per hour per IP

When rate limit is exceeded:
```json
{
  "error": "Rate limit exceeded"
}
```

Status Code: `429 Too Many Requests`

---

## Algorithm Details

### K-Means Clustering
1. Groups comics into K clusters based on genre features and user ratings
2. Finds similar comics within the same cluster
3. Predicts ratings using weighted collaborative filtering
4. Returns comics with predicted rating ≥ 3.0 (configurable)

**Parameters:**
- `KMEANS_CLUSTERS`: Number of clusters (default: 2)
- `KNN_K`: Number of nearest neighbors (default: 10)

### DBSCAN Clustering
1. Uses density-based clustering to group similar comics
2. Automatically determines number of clusters
3. Identifies outliers as noise points
4. Predicts ratings using weighted collaborative filtering
5. Returns comics with predicted rating ≥ 3.0 (configurable)

**Parameters:**
- `DBSCAN_EPSILON`: Maximum distance between neighbors (default: 7.8)
- `KNN_K`: Number of nearest neighbors (default: 10)

---

## Performance

**Expected Response Times:**
- Health check: < 10ms
- K-Means recommendation: 1-5 seconds
- DBSCAN recommendation: 1-5 seconds

Response time depends on:
- Number of input ratings
- Dataset size
- Server resources
- Number of predictions to generate

---

## CORS

Cross-Origin Resource Sharing (CORS) is enabled.

Default: All origins allowed (`*`)

Configure via `CORS_ORIGINS` environment variable.
