.PHONY: dev test build run lock

dev:
	pip install -r requirements.lock
	pip install -e .[dev]

test:
	pytest

build:
	docker build -t pokemon-rarity .

run:
        pokemon-rarity --limit 1 --dry-run

lock:
	pip-compile --extra=dev --output-file=requirements.lock pyproject.toml
