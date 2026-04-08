.PHONY: test lint fmt

test:
	python3 -m pytest -q

lint:
	python3 -m ruff check .

fmt:
	python3 -m black .