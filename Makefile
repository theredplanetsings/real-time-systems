.PHONY: test lint fmt

test:
	python3 -m pytest -q tests

lint:
	python3 -m ruff check .

fmt:
	python3 -m black .