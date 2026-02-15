def _auth_headers():
    return {"X-API-Key": "test-token"}


def test_index_returns_welcome(app_client):
    response = app_client.get("/")
    assert response.status_code == 200
    assert b"WELCOME TO KAPPA" in response.data


def test_health_returns_ok(app_client):
    response = app_client.get("/health")
    assert response.status_code == 200


def test_api_requires_auth_token(app_client):
    response = app_client.get("/api/comics")
    assert response.status_code == 401


def test_api_rejects_wrong_token(app_client):
    response = app_client.get("/api/comics", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_post_comics_single(app_client):
    payload = {"comic_id": 99, "title": "New", "image_url": "https://img/99"}
    response = app_client.post("/api/comics", json=payload, headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert data["updated"] == 1


def test_post_comics_batch(app_client):
    payload = [
        {"comic_id": 101, "title": "Batch 1", "image_url": "https://img/101"},
        {"comic_id": 102, "title": "Batch 2", "image_url": "https://img/102"},
    ]
    response = app_client.post("/api/comics", json=payload, headers=_auth_headers())
    assert response.status_code == 200
    assert response.get_json()["updated"] == 2


def test_get_comics_list(app_client):
    response = app_client.get("/api/comics", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_get_comic_by_id(app_client):
    response = app_client.get("/api/comics/1", headers=_auth_headers())
    assert response.status_code == 200
    assert response.get_json()["id"] == 1


def test_get_comic_not_found(app_client):
    response = app_client.get("/api/comics/9999", headers=_auth_headers())
    assert response.status_code == 404


def test_post_comic_genres(app_client):
    payload = {"comic_id": 1, "Action": 1, "Drama": 1}
    response = app_client.post(
        "/api/comics/genres", json=payload, headers=_auth_headers()
    )
    assert response.status_code == 200
    assert response.get_json()["updated"] == 1


def test_post_ratings(app_client):
    payload = {"username": "dana", "comic_id": 1, "rating": 4}
    response = app_client.post("/api/ratings", json=payload, headers=_auth_headers())
    assert response.status_code == 200
    assert response.get_json()["inserted"] == 1


def test_post_ratings_missing_fields(app_client):
    payload = {"comic_id": 1, "rating": 4}
    response = app_client.post("/api/ratings", json=payload, headers=_auth_headers())
    assert response.status_code == 400


def test_precompute_status_before_compute(app_client):
    response = app_client.get("/api/precompute/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert data["kmeans"] is None
    assert data["dbscan"] is None


def test_precompute_single_method(app_client):
    response = app_client.post(
        "/api/precompute", json={"method": "kmeans"}, headers=_auth_headers()
    )
    assert response.status_code == 200


def test_precompute_invalid_method(app_client):
    response = app_client.post(
        "/api/precompute", json={"method": "unknown"}, headers=_auth_headers()
    )
    assert response.status_code == 400


def test_precompute_status_after_compute(app_client):
    app_client.post("/api/precompute", headers=_auth_headers())
    response = app_client.get("/api/precompute/status", headers=_auth_headers())
    data = response.get_json()
    assert data["kmeans"] is not None
    assert data["dbscan"] is not None


def test_kmeans_recommendation_requires_precompute(app_client):
    response = app_client.post(
        "/api/kmeans",
        json=[{"comic_id": 1, "rating": 5}],
        headers=_auth_headers(),
    )
    assert response.status_code == 503


def test_kmeans_recommendation(precomputed_client):
    response = precomputed_client.post(
        "/api/kmeans",
        json=[{"comic_id": 1, "rating": 5}],
        headers=_auth_headers(),
    )
    assert response.status_code == 200


def test_dbscan_recommendation(precomputed_client):
    response = precomputed_client.post(
        "/api/dbscan",
        json=[{"comic_id": 1, "rating": 5}],
        headers=_auth_headers(),
    )
    assert response.status_code == 200
