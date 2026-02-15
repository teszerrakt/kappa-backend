.PHONY: venv sync test lint migrate precompute run

venv:
	uv venv

sync:
	uv pip sync uv.lock

test:
	PYTHONPATH=./src pytest

migrate:
	PYTHONPATH=./src python src/scripts/migrate.py

precompute:
	curl -X POST http://localhost:80/api/precompute

run:
	PYTHONPATH=./src python wsgi.py
