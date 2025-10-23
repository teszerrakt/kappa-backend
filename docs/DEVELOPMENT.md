# Development Guide

This guide helps developers set up their development environment and contribute to Kappa Backend.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Debugging](#debugging)
- [Contributing](#contributing)

---

## Prerequisites

### Required Software
- **Python 3.11+**
- **pip** (Python package manager)
- **git**
- **Virtual environment** (venv or virtualenv)

### Optional Tools
- **Docker** (for containerized development)
- **Docker Compose** (for multi-container setup)
- **Visual Studio Code** or **PyCharm** (recommended IDEs)
- **Postman** or **curl** (for API testing)

---

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/teszerrakt/kappa-backend.git
cd kappa-backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (type checking, linting)
pip install mypy black flake8 pytest pytest-cov
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration for development
nano .env
```

Example `.env` for development:
```bash
DEBUG=True
HOST=0.0.0.0
PORT=80
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

### 5. Verify Setup

```bash
# Check Python syntax
python3 -m py_compile main.py

# Verify data files exist
ls -lh *.csv

# Run the application
python main.py
```

Application should start on `http://localhost:80`

---

## Project Structure

```
kappa-backend/
├── main.py                 # Flask application and API endpoints
├── predict.py              # Prediction algorithms (KNN, collaborative filtering)
├── cluster.py              # Clustering algorithms (K-Means, DBSCAN)
├── load_data.py            # Data loading and preprocessing
├── config.py               # Configuration management
├── logger.py               # Logging utilities
├── validation.py           # Input validation
├── utils.py                # Utility functions
├── wsgi.py                 # WSGI entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image configuration
├── .dockerignore           # Docker build exclusions
├── run.sh                  # Production startup script
├── .env.example            # Example environment variables
├── README.md               # Project overview
├── docs/
│   ├── API.md              # API documentation
│   ├── DEPLOYMENT.md       # Deployment guide
│   ├── DEVELOPMENT.md      # This file
│   └── CONFIGURATION.md    # Configuration reference
└── data files:
    ├── rating_5_min_75.csv     # User ratings data
    ├── comic_genre.csv         # Genre features
    └── firestore_comics.csv    # Comic metadata
```

### Module Descriptions

| Module | Purpose |
|--------|---------|
| **main.py** | Flask app initialization, API endpoints, request handling |
| **predict.py** | K-Nearest Neighbors, collaborative filtering, rating prediction |
| **cluster.py** | K-Means and DBSCAN clustering implementations |
| **load_data.py** | Data merging, user-item matrix creation |
| **config.py** | Centralized configuration with environment variables |
| **logger.py** | Structured logging setup |
| **validation.py** | Input validation, schema checking, error handling |
| **utils.py** | Helper functions (data loading, enrichment, filtering) |
| **wsgi.py** | Production WSGI application entry point |

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit the relevant Python files following the [Code Style](#code-style) guidelines.

### 3. Test Changes

```bash
# Start development server
python main.py

# Or with Flask dev server
export FLASK_APP=main.py
export FLASK_ENV=development
flask run --debug

# Test endpoints
curl -X POST http://localhost:80/api/kmeans \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### 4. Format and Lint

```bash
# Format code with Black
black *.py

# Check code style with Flake8
flake8 *.py --max-line-length=100

# Type checking with mypy
mypy main.py --ignore-missing-imports
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `chore:` - Build/tooling changes

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Code Style

### Python Style Guide

Follow **PEP 8** with these specific guidelines:

```python
# 1. Type Hints
def predict_rating(
    user_id: str,
    item_id: int,
    ratings: pd.DataFrame
) -> Dict[str, Any]:
    """
    Predict rating for user-item pair.

    Args:
        user_id: User identifier
        item_id: Item identifier
        ratings: DataFrame with ratings

    Returns:
        Dictionary with prediction

    Raises:
        ValueError: If invalid input
    """
    pass

# 2. Docstrings (Google Style)
"""
Brief function description.

Detailed explanation of what the function does,
including algorithm details if relevant.

Args:
    param1: Description of param1
    param2: Description of param2

Returns:
    Description of return value

Raises:
    ExceptionType: When this exception is raised
"""

# 3. Imports
# Standard library
import os
import sys
from typing import Dict, List, Any

# Third-party
import pandas as pd
import numpy as np

# Local modules
from config import Config
from logger import get_logger

# 4. Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# 5. Naming Conventions
class UserRecommender:  # PascalCase for classes
    def predict_ratings(self):  # snake_case for functions
        max_rating = 5.0  # snake_case for variables

# 6. Line Length
# Maximum 100 characters per line
```

### Formatting Tools

```bash
# Auto-format with Black
black *.py

# Sort imports with isort
isort *.py

# Check style with Flake8
flake8 *.py --max-line-length=100 --extend-ignore=E203,W503
```

### VS Code Configuration

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=100"],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "editor.formatOnSave": true,
  "python.linting.mypyEnabled": true
}
```

---

## Testing

### Manual Testing

```bash
# Start server
python main.py

# Test health endpoint
curl http://localhost:80/health

# Test K-Means endpoint
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

### Unit Testing (Future)

Create `tests/` directory:

```python
# tests/test_validation.py
import pytest
from validation import validate_user_input, ValidationError

def test_validate_user_input_valid():
    input_data = [
        {"id": 1, "rating": 5.0},
        {"id": 2, "rating": 4.0},
        {"id": 3, "rating": 3.5},
        {"id": 4, "rating": 4.5},
        {"id": 5, "rating": 5.0}
    ]
    result = validate_user_input(input_data)
    assert len(result) == 5

def test_validate_user_input_too_few():
    input_data = [
        {"id": 1, "rating": 5.0}
    ]
    with pytest.raises(ValidationError):
        validate_user_input(input_data)

# Run tests
pytest tests/ -v --cov
```

### Integration Testing

```python
# tests/test_integration.py
import requests

BASE_URL = "http://localhost:80"

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_kmeans_recommendation():
    ratings = [
        {"id": 44489, "rating": 5.0},
        {"id": 72025, "rating": 4.5},
        {"id": 13, "rating": 5.0},
        {"id": 21, "rating": 4.0},
        {"id": 1706, "rating": 4.5}
    ]
    response = requests.post(f"{BASE_URL}/api/kmeans", json=ratings)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Run load test
ab -n 1000 -c 10 -T application/json -p test_data.json \
  http://localhost:80/api/kmeans
```

---

## Debugging

### Enable Debug Mode

```python
# In main.py or via environment
app.run(debug=True, host='0.0.0.0', port=80)
```

Or set in `.env`:
```bash
DEBUG=True
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

### Logging

```python
from logger import get_logger

logger = get_logger(__name__)

# Debug messages
logger.debug("Processing user input")

# Info messages
logger.info(f"Generated {len(predictions)} recommendations")

# Warning messages
logger.warning(f"Item {item_id} not found in cluster")

# Error messages
logger.error(f"Failed to predict rating: {e}", exc_info=True)
```

### Python Debugger (pdb)

```python
import pdb

def predict_rating(user_id, item_id):
    # Set breakpoint
    pdb.set_trace()

    # Your code here
    prediction = calculate_prediction()
    return prediction
```

Commands:
- `n` - Next line
- `s` - Step into function
- `c` - Continue execution
- `p variable` - Print variable
- `l` - List code
- `q` - Quit debugger

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "main.py",
        "FLASK_ENV": "development"
      },
      "args": ["run", "--no-debugger", "--no-reload"],
      "jinja": true
    }
  ]
}
```

---

## Docker Development

### Build Development Image

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install dev dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    pip install mypy black flake8 pytest ipython

# Copy code
COPY . .

# Use Flask dev server
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -f Dockerfile.dev -t kappa-dev .
docker run -it -p 80:80 -v $(pwd):/app kappa-dev
```

### Docker Compose for Development

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  kappa-backend:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
    ports:
      - "80:80"
    environment:
      - DEBUG=True
      - LOG_LEVEL=DEBUG
    command: python main.py
```

---

## Performance Profiling

### Using cProfile

```python
import cProfile
import pstats

def profile_recommendation():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = process_recommendations(user_input, 'kmeans')

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

profile_recommendation()
```

### Memory Profiling

```bash
pip install memory_profiler

# Add decorator to function
from memory_profiler import profile

@profile
def process_recommendations(user_input, algorithm):
    # Your code
    pass

# Run with profiler
python -m memory_profiler main.py
```

---

## Common Development Tasks

### Add New Algorithm

1. Add algorithm function to `cluster.py` or `predict.py`
2. Add configuration in `config.py`
3. Add validation in `validation.py`
4. Update `main.py` endpoint logic
5. Update documentation
6. Add tests

### Add New Endpoint

```python
# In main.py
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint() -> Tuple[Response, int]:
    """
    Description of new endpoint.
    """
    try:
        # Get and validate input
        user_input = request.get_json()
        validated = validate_user_input(user_input)

        # Process request
        result = process_request(validated)

        logger.info("Request completed successfully")
        return jsonify(result), 200

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
```

### Modify Configuration

1. Add new config in `config.py`:
```python
class Config:
    NEW_PARAMETER: int = int(os.getenv('NEW_PARAMETER', '10'))
```

2. Update `.env.example`
3. Update documentation
4. Use in code: `Config.NEW_PARAMETER`

---

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes following code style guidelines
4. Test thoroughly
5. Commit with descriptive messages
6. Push to your fork
7. Create Pull Request with:
   - Clear description of changes
   - Link to related issues
   - Test results
   - Screenshots (if UI changes)

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance acceptable

---

## Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Scikit-learn Documentation](https://scikit-learn.org/stable/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [Black](https://black.readthedocs.io/) - Code formatter
- [mypy](https://mypy.readthedocs.io/) - Type checker
- [pytest](https://docs.pytest.org/) - Testing framework

### Learning Resources
- [K-Means Clustering](https://scikit-learn.org/stable/modules/clustering.html#k-means)
- [DBSCAN](https://scikit-learn.org/stable/modules/clustering.html#dbscan)
- [Collaborative Filtering](https://en.wikipedia.org/wiki/Collaborative_filtering)

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/teszerrakt/kappa-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/teszerrakt/kappa-backend/discussions)
- **Email**: [Your contact email]

Happy coding! 🚀
