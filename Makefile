.PHONY: test quick-test lint fmt fmt-check smoke check ci help

QUALITY_PATHS = pages tests streamlit_app.py st_helpers.py compare_utils.py

help:
	@echo "Real-Time Systems - Available Targets:"
	@echo ""
	@echo "  make test         - Run full test suite"
	@echo "  make quick-test   - Run core test subset (faster)"
	@echo "  make smoke        - Run Streamlit smoke tests"
	@echo "  make lint         - Check code quality with ruff"
	@echo "  make fmt          - Auto-format code with black"
	@echo "  make fmt-check    - Check code formatting without changes"
	@echo "  make check        - Run lint, fmt-check, and full tests"
	@echo "  make ci           - Run full CI pipeline (same as check)"
	@echo ""

test:
	python3 -m pytest -q tests

quick-test:
	python3 -m pytest -q tests/test_schedulability_core.py tests/test_compare_metrics.py tests/test_scheduling_math.py

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