.PHONY: dev test build run

dev:
	pip install -r requirements.lock
	pip install -e .[dev]

test:
	pytest

build:
	docker build -t pokemon-rarity .

run:
	pokemon-rarity --limit 1 --dry-run
