# Deployment Guide

This guide covers various deployment options for Kappa Backend.

## Table of Contents
- [Docker Deployment](#docker-deployment)
- [Docker Compose](#docker-compose)
- [Manual Deployment](#manual-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Monitoring](#monitoring)

---

## Docker Deployment

### Using Pre-built Image

```bash
# Pull the image
docker pull teszerrakt/kappa-api

# Run the container
docker run -d \
  --name kappa-backend \
  -p 80:8000 \
  -e LOG_LEVEL=info \
  teszerrakt/kappa-api
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/teszerrakt/kappa-backend.git
cd kappa-backend

# Build the image
docker build -t kappa-backend:latest .

# Run the container
docker run -d \
  --name kappa-backend \
  -p 80:8000 \
  -e LOG_LEVEL=info \
  kappa-backend:latest
```

### Docker Run with Configuration

```bash
docker run -d \
  --name kappa-backend \
  -p 80:8000 \
  -e DEBUG=False \
  -e LOG_LEVEL=info \
  -e KMEANS_CLUSTERS=2 \
  -e DBSCAN_EPSILON=7.8 \
  -e KNN_K=10 \
  -e MIN_RATING_THRESHOLD=3.0 \
  --restart unless-stopped \
  --health-cmd "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")'" \
  --health-interval=30s \
  --health-timeout=3s \
  --health-retries=3 \
  kappa-backend:latest
```

---

## Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  kappa-backend:
    image: teszerrakt/kappa-api:latest
    # OR build from source:
    # build: .
    container_name: kappa-backend
    ports:
      - "80:8000"
    environment:
      - DEBUG=False
      - LOG_LEVEL=info
      - KMEANS_CLUSTERS=2
      - DBSCAN_EPSILON=7.8
      - KNN_K=10
      - MIN_RATING_THRESHOLD=3.0
      - CORS_ORIGINS=*
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: kappa-nginx
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - kappa-backend
    restart: unless-stopped
```

Deploy with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f kappa-backend

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

---

## Manual Deployment

### Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

### Setup

```bash
# Clone repository
git clone https://github.com/teszerrakt/kappa-backend.git
cd kappa-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

### Running with Gunicorn (Production)

```bash
# Using run.sh script
chmod +x run.sh
./run.sh

# Or directly with gunicorn
gunicorn wsgi:app \
  --bind 0.0.0.0:80 \
  --workers 4 \
  --worker-class sync \
  --timeout 120 \
  --log-level info \
  --access-logfile - \
  --error-logfile - \
  --preload
```

### Running with Flask Development Server

**⚠️ Not recommended for production!**

```bash
export FLASK_APP=main.py
export FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=80
```

---

## Cloud Deployment

### AWS EC2

```bash
# Connect to EC2 instance
ssh -i key.pem ubuntu@your-ec2-instance.com

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Deploy application
git clone https://github.com/teszerrakt/kappa-backend.git
cd kappa-backend
docker-compose up -d

# Configure security group to allow port 80/443
```

### AWS ECS (Elastic Container Service)

1. Push image to ECR:
```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag kappa-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/kappa-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/kappa-backend:latest
```

2. Create ECS task definition with:
   - Container image: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/kappa-backend:latest`
   - Port mapping: 8000
   - Environment variables (see Configuration)
   - Health check: `/health`

3. Create ECS service with Application Load Balancer

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/kappa-backend

# Deploy to Cloud Run
gcloud run deploy kappa-backend \
  --image gcr.io/PROJECT_ID/kappa-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars LOG_LEVEL=info,KMEANS_CLUSTERS=2
```

### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create kappa-backend-app

# Set environment variables
heroku config:set LOG_LEVEL=info
heroku config:set KMEANS_CLUSTERS=2

# Deploy
git push heroku main

# Scale dynos
heroku ps:scale web=2
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Configure build:
   - Dockerfile: `Dockerfile`
   - HTTP Port: 8000
3. Set environment variables
4. Deploy

---

## Environment Variables

Create `.env` file or set environment variables:

```bash
# Flask Configuration
DEBUG=False
HOST=0.0.0.0
PORT=80
FLASK_ENV=production

# Data Files (for manual deployment)
DATA_DIR=/app
RATING_FILE=rating_5_min_75.csv
GENRE_FILE=comic_genre.csv
COMIC_FILE=firestore_comics.csv

# Algorithm Hyperparameters
KMEANS_CLUSTERS=2
DBSCAN_EPSILON=7.8
KNN_K=10
MIN_RATING_THRESHOLD=3.0

# Validation
MIN_USER_RATINGS=5
MAX_USER_RATINGS=1000

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=*

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100 per hour
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed explanation.

---

## Health Checks

The `/health` endpoint provides service status:

```bash
# Check health
curl http://localhost:80/health

# Response
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

Configure monitoring tools to check this endpoint:

**Docker:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 3s
  retries: 3
```

**Kubernetes:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Monitoring

### Logging

Logs are written to stdout/stderr in JSON format:

```bash
# Docker logs
docker logs -f kappa-backend

# Follow logs with timestamps
docker logs -f --timestamps kappa-backend

# Last 100 lines
docker logs --tail 100 kappa-backend
```

### Log Aggregation

**ELK Stack (Elasticsearch, Logstash, Kibana):**
```yaml
services:
  kappa-backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Datadog:**
```bash
docker run -d \
  --name kappa-backend \
  --label com.datadoghq.ad.logs='[{"source": "python", "service": "kappa-backend"}]' \
  kappa-backend:latest
```

### Metrics

Monitor these metrics:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (5xx responses)
- Memory usage
- CPU usage
- Active connections

**Prometheus Example:**
Add `prometheus-flask-exporter` to monitor Flask metrics.

---

## Nginx Reverse Proxy

Example `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream kappa_backend {
        server kappa-backend:8000;
    }

    server {
        listen 80;
        server_name api.example.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.example.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Proxy settings
        location / {
            proxy_pass http://kappa_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check
        location /health {
            proxy_pass http://kappa_backend/health;
            access_log off;
        }
    }
}
```

---

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure proper `LOG_LEVEL` (info or warning)
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure CORS origins (don't use `*` in production)
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up automated backups for data files
- [ ] Configure health checks
- [ ] Set resource limits (CPU, memory)
- [ ] Enable auto-restart on failure
- [ ] Document runbooks for common issues
- [ ] Set up staging environment
- [ ] Implement CI/CD pipeline
- [ ] Security audit and penetration testing

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs kappa-backend

# Common issues:
# - Missing data files (rating_5_min_75.csv, etc.)
# - Insufficient memory
# - Port already in use
```

### High memory usage
```bash
# Reduce workers
export WORKERS=2

# Or limit Docker memory
docker run -m 2g kappa-backend:latest
```

### Slow responses
- Increase worker count
- Add more CPU/memory
- Enable caching
- Optimize clustering parameters

### Data file errors
```bash
# Verify files exist
docker exec kappa-backend ls -lh *.csv

# Check file permissions
docker exec kappa-backend ls -l *.csv
```

---

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```yaml
version: '3.8'
services:
  kappa-backend:
    image: kappa-backend:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
```

### Load Balancing with Nginx

```nginx
upstream kappa_backend {
    least_conn;
    server kappa-backend-1:8000;
    server kappa-backend-2:8000;
    server kappa-backend-3:8000;
}
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kappa-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kappa-backend
  template:
    metadata:
      labels:
        app: kappa-backend
    spec:
      containers:
      - name: kappa-backend
        image: kappa-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

---

## Support

For deployment issues, please check:
- [GitHub Issues](https://github.com/teszerrakt/kappa-backend/issues)
- [API Documentation](API.md)
- [Configuration Reference](CONFIGURATION.md)
