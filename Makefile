.PHONY: test lint fmt fmt-check smoke check ci

QUALITY_PATHS = pages tests streamlit_app.py st_helpers.py compare_utils.py

test:
	python3 -m pytest -q tests

lint:
	python3 -m ruff check --select F,B $(QUALITY_PATHS)

fmt:
	python3 -m black $(QUALITY_PATHS)

fmt-check:
	python3 -m black --check $(QUALITY_PATHS)

smoke:
	python3 -m pytest -q tests/test_streamlit_smoke.py

check: lint fmt-check test

ci: check