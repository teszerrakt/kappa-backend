# Kappa Backend

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://hub.docker.com/r/teszerrakt/kappa-api)

**Kappa Backend** is a production-ready RESTful API for comic recommendations using advanced machine learning algorithms. It implements cluster-based collaborative filtering with K-Means and DBSCAN clustering to provide personalized comic recommendations.

---

## 🎯 Features

- **🤖 Advanced ML Algorithms**
  - K-Means clustering for efficient comic grouping
  - DBSCAN density-based clustering for outlier detection
  - K-Nearest Neighbors collaborative filtering
  - Genre-enhanced feature matrix for better clustering

- **🏗️ Production-Ready Architecture**
  - Comprehensive error handling and validation
  - Structured logging for monitoring
  - Type hints and extensive documentation
  - Configuration management with environment variables
  - Health check endpoint with detailed status

- **🔒 Security & Performance**
  - Input validation and sanitization
  - Rate limiting support
  - CORS configuration
  - Docker containerization with non-root user
  - Optimized DataFrame operations

- **📊 Developer Experience**
  - Clean, DRY codebase following best practices
  - Comprehensive API documentation
  - Multiple deployment options
  - Detailed configuration reference

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Pull and run the latest image
docker pull teszerrakt/kappa-api
docker run -d -p 80:8000 --name kappa-backend teszerrakt/kappa-api

# Verify it's running
curl http://localhost:80/health
```

### Using Python

```bash
# Clone repository
git clone https://github.com/teszerrakt/kappa-backend.git
cd kappa-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The API will be available at `http://localhost:80`

---

## 📡 API Endpoints

### Health Check
```http
GET /health
```

Returns service status and data statistics.

### K-Means Recommendations
```http
POST /api/kmeans
Content-Type: application/json

[
  {"id": 44489, "rating": 5.0, "title": "Naruto"},
  {"id": 72025, "rating": 4.5, "title": "One Piece"},
  {"id": 13, "rating": 5.0, "title": "Attack on Titan"},
  {"id": 21, "rating": 4.0, "title": "Death Note"},
  {"id": 1706, "rating": 4.5, "title": "Fullmetal Alchemist"}
]
```

### DBSCAN Recommendations
```http
POST /api/dbscan
```

Same format as K-Means. Returns recommended comics sorted by predicted rating.

**Requirements:**
- Minimum 5 ratings (configurable)
- Rating values between 1.0 and 5.0
- Returns comics with predicted rating ≥ 3.0

---

## 💡 Example Usage

### cURL
```bash
curl -X POST http://localhost:80/api/kmeans \
  -H "Content-Type: application/json" \
  -d '[
    {"id": 44489, "rating": 5.0},
    {"id": 72025, "rating": 4.5},
    {"id": 13, "rating": 5.0},
    {"id": 21, "rating": 4.0},
    {"id": 1706, "rating": 4.5}
  ]'
```

### Python
```python
import requests

ratings = [
    {"id": 44489, "rating": 5.0},
    {"id": 72025, "rating": 4.5},
    {"id": 13, "rating": 5.0},
    {"id": 21, "rating": 4.0},
    {"id": 1706, "rating": 4.5}
]

response = requests.post('http://localhost:80/api/kmeans', json=ratings)
recommendations = response.json()

for comic in recommendations:
    print(f"{comic['title']}: {comic['rating']:.2f}")
```

---

## 🎨 Demo

Try the full application at **[kappa.zsyihab.tech](https://kappa.zsyihab.tech)**

**Note:** You need to input a minimum of five comics to get recommendations.

---

## 📦 Project Structure

```
kappa-backend/
├── main.py                  # Flask app & API endpoints
├── predict.py               # KNN collaborative filtering
├── cluster.py               # K-Means & DBSCAN clustering
├── load_data.py             # Data loading & preprocessing
├── config.py                # Configuration management
├── logger.py                # Structured logging
├── validation.py            # Input validation
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docs/                    # Documentation
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   └── CONFIGURATION.md
└── ...
```

---

## ⚙️ Configuration

Create a `.env` file or set environment variables:

```bash
# Algorithm Parameters
KMEANS_CLUSTERS=2          # Number of K-Means clusters
DBSCAN_EPSILON=7.8         # DBSCAN epsilon parameter
KNN_K=10                   # Number of nearest neighbors
MIN_RATING_THRESHOLD=3.0   # Minimum rating to recommend

# Validation
MIN_USER_RATINGS=5         # Minimum input ratings required

# Logging
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR

# CORS
CORS_ORIGINS=*             # Allowed origins
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete reference.

---

## 🐳 Docker Deployment

```bash
docker run -d \
  --name kappa-backend \
  -p 80:8000 \
  -e LOG_LEVEL=info \
  -e KMEANS_CLUSTERS=2 \
  --restart unless-stopped \
  teszerrakt/kappa-api:latest
```

---

## 📚 Documentation

- **[API Documentation](docs/API.md)** - Complete API reference with examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Docker, cloud, and manual deployment
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, workflow, and contributing
- **[Configuration Reference](docs/CONFIGURATION.md)** - All configuration options

---

## 🤖 How It Works

### K-Means Algorithm
1. Groups comics into K clusters based on genre features and user ratings
2. Finds similar comics within the same cluster using KNN
3. Predicts ratings using weighted collaborative filtering
4. Returns comics with predicted rating ≥ threshold

### DBSCAN Algorithm
1. Uses density-based clustering to group similar comics
2. Automatically determines number of clusters
3. Identifies outliers as noise points
4. Predicts ratings using collaborative filtering

---

## 🤝 Contributing

Contributions are welcome! See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for guidelines.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/teszerrakt/kappa-backend/issues)
- **Demo**: [kappa.zsyihab.tech](https://kappa.zsyihab.tech)
- **Documentation**: [docs/](docs/)

---

<div align="center">

**[Documentation](docs/)** • **[API Reference](docs/API.md)** • **[Deployment](docs/DEPLOYMENT.md)** • **[Contributing](docs/DEVELOPMENT.md)**

Made with ❤️ for comic enthusiasts

</div>
