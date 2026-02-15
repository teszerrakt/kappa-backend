import importlib


def test_normalize_comic_id_uses_comic_id(monkeypatch):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    importlib.reload(main)
    assert main._normalize_comic_id({"comic_id": 10}) == 10


def test_normalize_comic_id_uses_id(monkeypatch):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    importlib.reload(main)
    assert main._normalize_comic_id({"id": 11}) == 11


def test_validate_user_input(monkeypatch):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    importlib.reload(main)
    assert main._validate_user_input([{"id": 1, "rating": 4}]) is None


def test_validate_user_input_missing_id(monkeypatch):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    importlib.reload(main)
    assert main._validate_user_input([{"rating": 4}])


def test_invalidate_precomputed_cache(monkeypatch):
    monkeypatch.setenv("KAPPA_API_TOKEN", "test-token")
    from kappa import main

    importlib.reload(main)
    main._precomputed_cache["kmeans"] = {"data": "x"}
    main._invalidate_precomputed_cache("kmeans")
    assert "kmeans" not in main._precomputed_cache
