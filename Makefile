.PHONY: dev test build run lock debug e2e diag

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

debug:
        streamlit run app.py

e2e:
        python tests/rapid_toggle_e2e.py

diag:
        python app/diag/stale_write_demo.py
